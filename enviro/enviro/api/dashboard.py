import frappe
import requests
from frappe.utils import flt, getdate, today

WEATHER_CITY = "Sydney"


@frappe.whitelist(allow_guest=False)
def get_home_dashboard_data():
	"""
	Main function wrapped in safety nets. If one widget fails,
	the rest of the dashboard will still load perfectly.
	"""
	data = {
		"notifications": [],
		"all_jobs": [],
		"todays_schedule": [],
		"weather": {"error": "Unavailable"},
		"sales_data": None,
		"safety_data": {
			"people": {"mtd": 0, "ytd": 4, "lti": "no Data", "mtd_val": "no Data", "fti": 0},
			"vehicle": {"mtd": 1, "ytd": 3, "fault": 0, "non_fault": 0},
		},
	}

	# Safely load each section
	try:
		data["notifications"] = get_recent_activities()
	except Exception:
		pass

	try:
		data["all_jobs"] = get_all_jobs_summary()
	except Exception as e:
		data["all_jobs"] = [{"code": "Error", "title": str(e), "status": "Failed"}]

	try:
		data["todays_schedule"] = get_todays_appointments()
	except Exception:
		pass

	try:
		data["weather"] = get_weather_data()
	except Exception:
		pass

	try:
		data["sales_data"] = get_sales_data()
	except Exception:
		pass

	return data


def get_all_jobs_summary():
	# Efficient list query to avoid permission traps and slow get_doc loops
	jobs = frappe.get_list(
		"Enviro Job",
		fields=["name", "customer", "status"],
		limit=10,
		order_by="creation desc",
		ignore_permissions=True,
	)

	result = []
	for j in jobs:
		customer = j.get("customer")
		title = customer if customer else "No Customer"
		status = j.get("status", "Pending")

		result.append({"code": j.name, "title": title, "status": status})

	return result


def get_todays_appointments():
	current_date = today()
	# Efficient list query
	appointments = frappe.get_list(
		"Enviro Job",
		fields=["name", "customer", "status", "scheduled_start_time", "scheduled_end_time"],
		filters={"scheduled_start_date": current_date},
		limit=6,
		order_by="scheduled_start_time asc",
		ignore_permissions=True,
	)

	result = []
	for appt in appointments:
		customer = appt.get("customer", "Unknown")
		status = appt.get("status", "Pending")
		start = str(appt.get("scheduled_start_time", ""))
		end = str(appt.get("scheduled_end_time", ""))

		# Format time for display (e.g., 09:00 - 11:00)
		time_label = f"{start[:5]} - {end[:5]}" if start and end else (start[:5] or "No Time")

		result.append(
			{"name": appt.name, "customer_name": customer, "time_label": time_label, "status": status}
		)
	return result


def get_recent_activities():
	# Fetch from both Quotations and Jobs
	logs = frappe.get_all(
		"Activity Log",
		fields=["name", "subject", "creation", "reference_doctype", "reference_name"],
		filters={
			"reference_doctype": ["in", ["Quotation", "Enviro Job"]],
		},
		limit=8,
		order_by="creation desc",
		ignore_permissions=True,
	)
	return [
		{
			"id": l.name,
			"title": l.subject,
			"timestamp": l.creation,
			"doctype": l.reference_doctype,
			"docname": l.reference_name,
		}
		for l in logs
	]


def get_sales_data():
	year = getdate().year
	sales = frappe.db.sql(
		"""
        SELECT MONTH(transaction_date) as month, SUM(grand_total) as total
        FROM `tabQuotation`
        WHERE YEAR(transaction_date) = %s AND docstatus = 1
        GROUP BY MONTH(transaction_date)
    """,
		(year,),
		as_dict=True,
	)

	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	values = [0] * 12
	for s in sales:
		values[s.month - 1] = flt(s.total)
	return {"labels": months, "datasets": [{"name": "Actual Sales", "values": values}]}


def get_weather_data(city=WEATHER_CITY):
	cache_key = f"enviro_weather_{city.lower().replace(' ', '_')}"
	cached_data = frappe.cache().get_value(cache_key)
	if cached_data:
		return cached_data

	geo = requests.get(
		"https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=2
	).json()
	if not geo.get("results"):
		return {"error": "City not found"}

	loc = geo["results"][0]
	wx = requests.get(
		"https://api.open-meteo.com/v1/forecast",
		params={
			"latitude": loc["latitude"],
			"longitude": loc["longitude"],
			"current": "temperature_2m,weather_code",
			"daily": "weather_code,temperature_2m_max",
			"forecast_days": 7,
			"timezone": "auto",
		},
		timeout=2,
	).json()

	res = {
		"city": loc["name"],
		"current_temp": round(wx["current"]["temperature_2m"]),
		"weather_code": wx["current"]["weather_code"],
		"daily": {
			"time": wx["daily"]["time"],
			"weather_code": wx["daily"]["weather_code"],
			"temp_max": [round(t) for t in wx["daily"]["temperature_2m_max"]],
		},
	}
	frappe.cache().set_value(cache_key, res, expires_in_sec=900)
	return res
