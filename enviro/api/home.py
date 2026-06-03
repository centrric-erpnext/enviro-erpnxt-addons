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
			"people": {
				"mtd": 0,
				"ytd": 4,
				"lti": "no Data",
				"mtd_val": "no Data",
				"fti": 0,
			},
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
		{
			"code": j.name,
			"title": j.get("customer") or "No Customer",
			"status": j.get("status", "Pending"),
		}
		for j in jobs
	]
	frappe.cache().set_value(cache_key, result, expires_in_sec=120)
	return result


def get_todays_appointments():
	current_date = today()
	appointments = frappe.get_list(
		"Enviro Job",
		fields=[
			"name",
			"customer",
			"status",
			"scheduled_start_time",
			"scheduled_end_time",
		],
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

	start_date = f"{year}-01-01"
	end_date = f"{year}-12-31"

	query = """
		SELECT MONTH(transaction_date) as month, SUM(grand_total) as total
		FROM `tabQuotation`
		WHERE transaction_date >= %s AND transaction_date <= %s AND docstatus = 1
	"""
	params = [start_date, end_date]

	if month:
		m_str = str(month).zfill(2)
		start_date = f"{year}-{m_str}-01"
		# Get the last day of the month
		import calendar

		last_day = calendar.monthrange(int(year), int(month))[1]
		end_date = f"{year}-{m_str}-{last_day}"

		query = """
			SELECT MONTH(transaction_date) as month, SUM(grand_total) as total
			FROM `tabQuotation`
			WHERE transaction_date >= %s AND transaction_date <= %s AND docstatus = 1
		"""
		params = [start_date, end_date]

	query += " GROUP BY MONTH(transaction_date)"

	sales = frappe.db.sql(query, tuple(params), as_dict=True)

	months_labels = [
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec",
	]
	values = [0] * 12
	for s in sales:
		if 1 <= s.month <= 12:
			values[s.month - 1] = flt(s.total)

	result = {
		"labels": months_labels,
		"datasets": [{"name": "Actual Sales", "values": values}],
	}
	frappe.cache().set_value(cache_key, result, expires_in_sec=600)  # 10 min cache
	return result


def get_weather_data(city=WEATHER_CITY):
	cache_key = f"enviro_weather_{city.lower().replace(' ', '_')}_wttr"
	cached_data = frappe.cache().get_value(cache_key)
	if cached_data:
		return cached_data

	try:
		res = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
		res.raise_for_status()
		data = res.json()

		# WWO to WMO mapping approximation
		def wwo_to_wmo(code):
			c = str(code)
			if c in ["113"]:
				return 0  # Clear
			if c in ["116"]:
				return 2  # Partly cloudy
			if c in ["119", "122"]:
				return 3  # Overcast
			if c in ["143", "248", "260"]:
				return 45  # Fog
			if c in ["176", "263", "266", "293", "296", "299", "302", "305", "308"]:
				return 61  # Rain
			if c in ["200", "386", "389", "392", "395"]:
				return 95  # Thunderstorm
			if c in ["227", "230", "323", "326", "329", "332", "335", "338"]:
				return 71  # Snow
			return 3  # Default cloudy

		curr = data["current_condition"][0]
		w_code = wwo_to_wmo(curr.get("weatherCode", "113"))

		times = []
		codes = []
		temps = []

		# wttr.in returns 3 days
		for day in data.get("weather", []):
			times.append(day.get("date"))
			hourly = day.get("hourly", [{}])[0]
			codes.append(wwo_to_wmo(hourly.get("weatherCode", "113")))
			temps.append(round(float(day.get("maxtempC", 0))))

		# Pad to 7 days
		if len(times) > 0:
			while len(times) < 7:
				from datetime import datetime, timedelta

				last_date = datetime.strptime(times[-1], "%Y-%m-%d")
				next_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
				times.append(next_date)
				codes.append(codes[-1])
				temps.append(temps[-1])

		res_data = {
			"city": city,
			"current_temp": round(float(curr.get("temp_C", 0))),
			"weather_code": w_code,
			"daily": {"time": times, "weather_code": codes, "temp_max": temps},
		}

		frappe.cache().set_value(cache_key, res_data, expires_in_sec=900)
		return res_data
	except Exception as e:
		frappe.log_error(title="Weather API Failed", message=str(e))
		return {"error": "Weather data unavailable"}
