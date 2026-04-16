import frappe
import requests
from frappe.utils import flt, getdate, now_datetime, today

WEATHER_CITY = "Melbourne"  # Change this to your actual city name


@frappe.whitelist(allow_guest=False)
def get_weather_data(city=None):
	"""
	Fetches live weather data from Open-Meteo (free, no API key required).
	"""
	city_name = city or WEATHER_CITY
	try:
		geo = requests.get(
			"https://geocoding-api.open-meteo.com/v1/search",
			params={"name": city_name, "count": 1, "language": "en", "format": "json"},
			timeout=5,
		).json()

		if not geo.get("results"):
			return {"error": f"City '{city_name}' not found"}

		loc = geo["results"][0]
		lat, lon, name = loc["latitude"], loc["longitude"], loc["name"]

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
	Combines notifications, jobs, schedule, weather, and real sales data.
	"""
	data = {
		"notifications": get_recent_activities(),
		"all_jobs": get_all_jobs_summary(),
		"todays_schedule": get_todays_appointments(),
		"weather": get_weather_data(),
		"safety_data": {
			"people": {"mtd": 0, "ytd": 4, "lti": "no Data", "mtd_val": "no Data", "fti": 0},
			"vehicle": {"mtd": 1, "ytd": 3, "fault": 0, "non_fault": 0},
		},
	}

	# --- REAL SALES DATA INTEGRATION ---
	year = getdate().year
	sales = frappe.db.sql(
		"""
        SELECT MONTH(posting_date) as month, SUM(grand_total) as total
        FROM `tabSales Invoice`
        WHERE YEAR(posting_date) = %s AND docstatus = 1
        GROUP BY MONTH(posting_date)
    """,
		(year,),
		as_dict=True,
	)

	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	values = [0] * 12
	for s in sales:
		values[s.month - 1] = flt(s.total)

	data["sales_data"] = {"labels": months, "datasets": [{"name": "Actual Sales", "values": values}]}

	return data


def get_recent_activities():
	activities = []
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
	return activities


def get_all_jobs_summary():
	jobs = frappe.get_all(
		"Enviro Job", fields=["name", "customer", "site", "status"], limit=6, order_by="creation desc"
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

	result = []
	for job in jobs:
		customer_name = customer_map.get(job.customer, "N/A") if job.customer else "N/A"
		site_name = site_map.get(job.site, "N/A") if job.site else "N/A"
		result.append(
			{"code": job.name, "title": customer_name, "description": site_name, "status": job.status}
		)
	return result


def get_todays_appointments():
	current_date = today()
	appointments = frappe.get_all(
		"Enviro Job",
		fields=["name", "customer", "site", "scheduled_start_time", "scheduled_end_time", "status"],
		filters={"scheduled_start_date": current_date},
		limit=4,  # Limited to 4 to fit perfectly in your 2x2 grid
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

	for appt in appointments:
		appt.customer_name = customer_map.get(appt.customer, "N/A") if appt.customer else "N/A"
		appt.site_name = site_map.get(appt.site, "") if appt.site else ""
		start = str(appt.scheduled_start_time or "")
		end = str(appt.scheduled_end_time or "")
		appt.time_label = f"{start[:5]} - {end[:5]}" if start and end else start[:5]

	return appointments
