import frappe


@frappe.whitelist()
def get_completed_jobs(from_date=None, to_date=None, search_txt=None):
	"""
	Fetches completed Enviro Jobs enriched with Quotation details for the Invoice Dashboard.
	Supports date range filtering and search by client name or job code.
	"""
	filters = {"status": "Completed"}

	if from_date and to_date and from_date != "undefined" and to_date != "undefined":
		filters["job_finished_time"] = [
			"between",
			[from_date + " 00:00:00", to_date + " 23:59:59"],
		]
	elif from_date and from_date != "undefined":
		filters["job_finished_time"] = [">=", from_date + " 00:00:00"]
	elif to_date and to_date != "undefined":
		filters["job_finished_time"] = ["<=", to_date + " 23:59:59"]

	# Fetch jobs
	jobs = frappe.get_all(
		"Enviro Job",
		filters=filters,
		fields=[
			"name",
			"quotation",
			"job_finished_time",
			"customer",
			"status",
			"owner",
		],
		order_by="job_finished_time desc",
		limit=100,  # Safety limit for performance
	)

	if not jobs:
		return []

	# Bulk fetch Quotation data to avoid N+1 queries
	quote_names = list(set([j.quotation for j in jobs if j.quotation]))
	quote_map = {}
	if quote_names:
		quotes = frappe.get_all(
			"Quotation",
			filters={"name": ["in", quote_names]},
			fields=["name", "customer_name", "grand_total", "owner"],
		)
		quote_map = {q.name: q for q in quotes}

	results = []
	search_txt_lower = search_txt.lower() if search_txt else None

	for j in jobs:
		q = quote_map.get(j.quotation, {})
		client_name = q.get("customer_name") or j.customer or "N/A"

		# Efficient Search Filter
		if search_txt_lower:
			match = (
				search_txt_lower in str(client_name).lower()
				or search_txt_lower in str(j.name).lower()
				or search_txt_lower in str(j.quotation or "").lower()
			)
			if not match:
				continue

		results.append(
			{
				"job_code": j.name,
				"quote_no": j.quotation,
				"completed_date": j.job_finished_time,
				"client_id": j.customer,
				"client_name": client_name,
				"quoted_by": q.get("owner") or j.owner,
				"quote_amt": q.get("grand_total") or 0,
				"job_status": "Job Finished",
				"status": j.status,
				"comments": "",
			}
		)

	return results


@frappe.whitelist()
def get_quotation_waste_types(quotation):
	"""
	Securely fetches aggregated waste types for a quotation.
	Used by Job Card to bypass strict client-side permission checks on child tables.
	"""
	if not quotation:
		return ""

	waste_types = frappe.db.sql(
		"""
		SELECT DISTINCT custom_waste_type
		FROM `tabQuotation Item`
		WHERE parent = %s AND custom_waste_type IS NOT NULL AND custom_waste_type != ''
	""",
		quotation,
		pluck=True,
	)

	return ", ".join(sorted(waste_types)) if waste_types else ""
