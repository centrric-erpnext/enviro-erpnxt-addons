import frappe
import requests
from frappe.utils import now_datetime, today

WEATHER_CITY = "Melbourne"  # Change this to your actual city name


@frappe.whitelist(allow_guest=False)
def get_weather_data(city=None):
	"""
	Fetches live weather data from Open-Meteo (free, no API key required).
	Runs server-side to avoid browser CSP/CORS restrictions.
	"""
	city_name = city or WEATHER_CITY
	try:
		# Step 1: Geocode city → lat/lon
		geo = requests.get(
			"https://geocoding-api.open-meteo.com/v1/search",
			params={"name": city_name, "count": 1, "language": "en", "format": "json"},
			timeout=5,
		).json()

		if not geo.get("results"):
			return {"error": f"City '{city_name}' not found"}

		loc = geo["results"][0]
		lat, lon, name = loc["latitude"], loc["longitude"], loc["name"]

		# Step 2: Fetch current + 7-day forecast
		wx = requests.get(
			"https://api.open-meteo.com/v1/forecast",
			params={
				"latitude": lat,
				"longitude": lon,
				"current": "temperature_2m,weather_code,apparent_temperature",
				"daily": "weather_code,temperature_2m_max,temperature_2m_min",
				"forecast_days": 7,
				"timezone": "auto",
			},
			timeout=5,
		).json()

		return {
			"city": name,
			"current_temp": round(wx["current"]["temperature_2m"]),
			"weather_code": wx["current"]["weather_code"],
			"daily": {
				"time": wx["daily"]["time"],
				"weather_code": wx["daily"]["weather_code"],
				"temp_max": [round(t) for t in wx["daily"]["temperature_2m_max"]],
				"temp_min": [round(t) for t in wx["daily"]["temperature_2m_min"]],
			},
		}
	except Exception as e:
		frappe.log_error(f"Weather fetch failed: {e}", "Enviro Weather")
		return {"error": str(e)}


@frappe.whitelist()
def get_home_dashboard_data():
	"""
	Combines notifications, jobs, schedule, weather data for the Home Workspace.
	"""
	return {
		"notifications": get_recent_activities(),
		"all_jobs": get_all_jobs_summary(),
		"todays_schedule": get_todays_appointments(),
		"weather": get_weather_data(),
		"sales_data": {
			"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
			"datasets": [{"name": "Actual Sales", "values": [12, 19, 23, 17, 28, 22, 35]}],
		},
		"safety_data": {
			"people": {"mtd": 0, "ytd": 4, "lti": "no Data", "mtd_val": "no Data", "fti": 0},
			"vehicle": {"mtd": 1, "ytd": 3, "fault": 0, "non_fault": 0},
		},
	}


def get_recent_activities():
	"""
	Fetches the last 6 activities based on status changes.
	Matches strings like 'Quote reviewed', 'Quote approved', 'Quotation Created'.
	"""
	activities = []

	# Target status keywords provided by user
	target_messages = ["Quote reviewed", "Quote approved", "Quotation Created"]

	# Instead of generic string matching which is extremely slow on large databases,
	# we will only grab recent logs matching the specific Quotation creation/review endpoints
	# OR explicitly matching the exact title strings natively to avoid loop processing.

	target_messages = ["Quote reviewed", "Quote approved", "Quotation Created"]
	filters = {"subject": ("in", target_messages), "reference_doctype": "Quotation"}

	logs = frappe.get_all(
		"Activity Log",
		fields=["name", "subject", "creation", "reference_doctype", "reference_name"],
		filters=filters,
		limit=6,
		order_by="creation desc",
	)

	for log in logs:
		activities.append(
			{
				"id": log.name,
				"title": log.subject,
				"timestamp": log.creation,
				"doctype": log.reference_doctype,
				"docname": log.reference_name,
			}
		)

	# If we still need more, grab exact Communication comments
	if len(activities) < 6:
		comms = frappe.get_all(
			"Communication",
			fields=["name", "subject", "content", "creation", "reference_doctype", "reference_name"],
			filters={"reference_doctype": "Quotation", "communication_type": "Comment"},
			limit=10,
			order_by="creation desc",
		)
		for comm in comms:
			if comm.content and any(msg.lower() in str(comm.content).lower() for msg in target_messages):
				activities.append(
					{
						"id": comm.name,
						"title": comm.subject or "Quotation Activity",
						"timestamp": comm.creation,
						"doctype": comm.reference_doctype,
						"docname": comm.reference_name,
					}
				)

	# Sort and slice optimally
	activities.sort(key=lambda x: str(x["timestamp"]), reverse=True)
	return activities[:6]


def get_all_jobs_summary():
	"""
	Returns latest Enviro Jobs with fields mapped for the Quick List.
	Code -> name
	Title -> customer (customer_name)
	Description -> site (site_name)
	"""
	jobs = frappe.get_all(
		"Enviro Job", fields=["name", "customer", "site", "status"], limit=10, order_by="creation desc"
	)

	customer_ids = list(set([j.customer for j in jobs if j.customer]))
	site_ids = list(set([j.site for j in jobs if j.site]))

	customer_map = {}
	site_map = {}

	if customer_ids:
		customers = frappe.get_all(
			"Customer", filters={"name": ("in", customer_ids)}, fields=["name", "customer_name"]
		)
		customer_map = {c.name: c.customer_name for c in customers}

	if site_ids:
		sites = frappe.get_all("Site", filters={"name": ("in", site_ids)}, fields=["name", "site_name"])
		site_map = {s.name: s.site_name for s in sites}

	# Enforce field mapping for frontend consistency
	result = []
	for job in jobs:
		customer_name = customer_map.get(job.customer, "N/A") if job.customer else "N/A"
		site_name = site_map.get(job.site, "N/A") if job.site else "N/A"

		result.append(
			{"code": job.name, "title": customer_name, "description": site_name, "status": job.status}
		)
	return result


def get_todays_appointments():
	"""
	Fetches today's appointments for the 2x2 grid.
	"""
	current_date = today()
	appointments = frappe.get_all(
		"Enviro Job",
		fields=["name", "customer", "site", "scheduled_start_time", "scheduled_end_time", "status"],
		filters={"scheduled_start_date": current_date},
		limit=6,
		order_by="scheduled_start_time asc",
	)

	customer_ids = list(set([a.customer for a in appointments if a.customer]))
	site_ids = list(set([a.site for a in appointments if a.site]))
	customer_map = {}
	site_map = {}
	if customer_ids:
		customers = frappe.get_all(
			"Customer", filters={"name": ("in", customer_ids)}, fields=["name", "customer_name"]
		)
		customer_map = {c.name: c.customer_name for c in customers}
	if site_ids:
		sites = frappe.get_all("Site", filters={"name": ("in", site_ids)}, fields=["name", "site_name"])
		site_map = {s.name: s.site_name for s in sites}

	# Polish formatting
	for appt in appointments:
		appt.customer_name = customer_map.get(appt.customer, "N/A") if appt.customer else "N/A"
		appt.site_name = site_map.get(appt.site, "") if appt.site else ""
		start = str(appt.scheduled_start_time or "")
		end = str(appt.scheduled_end_time or "")
		appt.time_label = f"{start[:5]} - {end[:5]}" if start and end else start[:5]

	return appointments
