import frappe


def fix_employee_profile():
	doc = frappe.get_doc("Custom HTML Block", "Enviro Employee Profile")
	script = doc.script
	script = script.replace(
		'.env-wrapper { display: flex; flex-direction: column; height: calc(100vh - 140px); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f9fafb; padding: 20px; border-radius: 8px; }\n        .env-wrapper > div:not(.env-table-container):not(.env-grid) { flex-shrink: 0; }',
		'.env-wrapper { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f9fafb; padding: 20px; border-radius: 8px; }',
	)
	doc.script = script
	doc.save()
	frappe.db.commit()
	print("Employee Profile Dashboard fixed successfully.")
