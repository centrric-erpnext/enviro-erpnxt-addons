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
	# Check cache first for the entire block (short expiry)
	cache_key = f"home_dashboard_data_{frappe.session.user}"
	cached = frappe.cache().get_value(cache_key)
	if cached:
		return cached

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
	data["notifications"] = _safe_exec(get_recent_activities, [])
	data["all_jobs"] = _safe_exec(get_all_jobs_summary, [])
	data["todays_schedule"] = _safe_exec(get_todays_appointments, [])
	data["weather"] = _safe_exec(get_weather_data, {"error": "Unavailable"})
	data["sales_data"] = _safe_exec(get_sales_data, None)

	frappe.cache().set_value(cache_key, data, expires_in_sec=300)  # 5 min cache
	return data


def _safe_exec(func, default):
	try:
		return func()
	except Exception:
		return default


def get_all_jobs_summary():
	# Cached for 2 minutes
	cache_key = "all_jobs_summary"
	cached = frappe.cache().get_value(cache_key)
	if cached:
		return cached

	jobs = frappe.get_list(
		"Enviro Job",
		fields=["name", "customer", "status"],
		limit=10,
		order_by="creation desc",
		ignore_permissions=True,
	)

	result = [
		{"code": j.name, "title": j.get("customer") or "No Customer", "status": j.get("status", "Pending")}
		for j in jobs
	]
	frappe.cache().set_value(cache_key, result, expires_in_sec=120)
	return result


def get_todays_appointments():
	current_date = today()
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
		start = str(appt.get("scheduled_start_time", ""))
		end = str(appt.get("scheduled_end_time", ""))
		time_label = f"{start[:5]} - {end[:5]}" if start and end else (start[:5] or "No Time")

		result.append(
			{
				"name": appt.name,
				"customer_name": appt.get("customer", "Unknown"),
				"time_label": time_label,
				"status": appt.get("status", "Pending"),
			}
		)
	return result


def get_recent_activities():
	logs = frappe.get_all(
		"Activity Log",
		fields=["name", "subject", "creation", "reference_doctype", "reference_name"],
		filters={"reference_doctype": ["in", ["Quotation", "Enviro Job"]]},
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


@frappe.whitelist()
def get_sales_data(year=None, month=None):
	"""
	Optimized sales data query.
	Supports filtering by year and optionally by month.
	"""
	if not year:
		year = getdate().year

	# Try to use frappe.get_all for better performance and security
	# but grand_total aggregation still needs raw SQL or heavy processing
	# We stick to SQL but optimize the query and cache the result.

	cache_key = f"sales_data_{year}_{month or 'all'}"
	cached = frappe.cache().get_value(cache_key)
	if cached:
		return cached

	query = """
		SELECT MONTH(transaction_date) as month, SUM(grand_total) as total
		FROM `tabQuotation`
		WHERE YEAR(transaction_date) = %s AND docstatus = 1
	"""
	params = [year]

	if month:
		query += " AND MONTH(transaction_date) = %s"
		params.append(month)

	query += " GROUP BY MONTH(transaction_date)"

	sales = frappe.db.sql(query, tuple(params), as_dict=True)

	months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	values = [0] * 12
	for s in sales:
		if 1 <= s.month <= 12:
			values[s.month - 1] = flt(s.total)

	result = {"labels": months_labels, "datasets": [{"name": "Actual Sales", "values": values}]}
	frappe.cache().set_value(cache_key, result, expires_in_sec=600)  # 10 min cache
	return result


def get_weather_data(city=WEATHER_CITY):
	cache_key = f"enviro_weather_{city.lower().replace(' ', '_')}"
	cached_data = frappe.cache().get_value(cache_key)
	if cached_data:
		return cached_data

	try:
		geo_res = requests.get(
			"https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=3
		)
		geo_res.raise_for_status()
		geo = geo_res.json()

		if not geo.get("results"):
			return {"error": "City not found"}

		loc = geo["results"][0]
		wx_res = requests.get(
			"https://api.open-meteo.com/v1/forecast",
			params={
				"latitude": loc["latitude"],
				"longitude": loc["longitude"],
				"current": "temperature_2m,weather_code",
				"daily": "weather_code,temperature_2m_max",
				"forecast_days": 7,
				"timezone": "auto",
			},
			timeout=3,
		)
		wx_res.raise_for_status()
		wx = wx_res.json()

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
	except Exception as e:
		frappe.log_error(f"Weather API Failed: {e!s}")
		return {"error": "Weather data unavailable"}
