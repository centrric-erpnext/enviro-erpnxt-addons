import frappe


def execute():
	dt = frappe.get_doc("DocType", "Enviro Job Card")

	def get_or_create(fieldname, label, fieldtype, options=None, depends_on=None):
		for f in dt.fields:
			if f.fieldname == fieldname:
				print(f"Modifying existing: {fieldname}")
				f.label = label
				f.fieldtype = fieldtype
				if options is not None:
					f.options = options
				if depends_on is not None:
					f.depends_on = depends_on
				return f

		print(f"Appending new: {fieldname}")
		return dt.append(
			"fields",
			{
				"fieldname": fieldname,
				"label": label,
				"fieldtype": fieldtype,
				"options": options,
				"depends_on": depends_on,
			},
		)

	# Update Industry Type
	for f in dt.fields:
		if f.fieldname == "industry_type":
			f.fieldtype = "Link"
			f.options = "Industry Type"
			print("Upgraded industry_type to Link")
			break

	# Update depends_on for frequency_in_weeks
	for f in dt.fields:
		if f.fieldname == "frequency_in_weeks":
			f.depends_on = "eval:doc.is_reoccurring_quote=='YES' && doc.type_of_reoccurring=='in Weeks Only'"
			print("Updated frequency_in_weeks visibility")
			break

	days_cond = "eval:doc.is_reoccurring_quote=='YES' && doc.type_of_reoccurring=='in Daily'"

	# Create the fields
	get_or_create(
		"type_of_reoccurring",
		"Type of Reoccurring",
		"Select",
		options="\nin Weeks Only\nin Daily",
		depends_on="eval:doc.is_reoccurring_quote=='YES'",
	)
	get_or_create("col_daily_1", "Days", "Column Break", depends_on=days_cond)
	get_or_create("monday", "Monday", "Check", depends_on=days_cond)
	get_or_create("tuesday", "Tuesday", "Check", depends_on=days_cond)
	get_or_create("wednesday", "Wednesday", "Check", depends_on=days_cond)
	get_or_create("thursday", "Thursday", "Check", depends_on=days_cond)
	get_or_create("col_daily_2", "", "Column Break", depends_on=days_cond)
	get_or_create("friday", "Friday", "Check", depends_on=days_cond)
	get_or_create("saturday", "Saturday", "Check", depends_on=days_cond)
	get_or_create("sunday", "Sunday", "Check", depends_on=days_cond)

	dt.save()
	frappe.db.commit()

	# Reorder sequentially for UX
	dt = frappe.get_doc("DocType", "Enviro Job Card")
	ordered_names = []

	new_injections = [
		"type_of_reoccurring",
		"col_daily_1",
		"monday",
		"tuesday",
		"wednesday",
		"thursday",
		"col_daily_2",
		"friday",
		"saturday",
		"sunday",
	]

	for f in dt.fields:
		if f.fieldname not in new_injections:
			ordered_names.append(f.fieldname)

			# Injection point: Before frequency_in_weeks
			if f.fieldname == "is_reoccurring_quote":
				ordered_names.append("type_of_reoccurring")

			# Injection point: After frequency_in_weeks
			if f.fieldname == "frequency_in_weeks":
				ordered_names.extend(
					[
						"col_daily_1",
						"monday",
						"tuesday",
						"wednesday",
						"thursday",
						"col_daily_2",
						"friday",
						"saturday",
						"sunday",
					]
				)

	# Rebuild fields list to exact order
	ordered_fields = []
	for oname in ordered_names:
		for f in dt.fields:
			if f.fieldname == oname:
				ordered_fields.append(f)
				break

	dt.fields = ordered_fields

	# Renumber the Frappe indices
	for i, f in enumerate(dt.fields):
		f.idx = i + 1

	dt.save()
	frappe.db.commit()
	print("Successfully mapped Job Card Schema!")
