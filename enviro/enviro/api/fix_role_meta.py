import frappe


def run():
	# Fix the field metadata to ensure it's a standard filter and in list view
	custom_field = frappe.get_doc("Custom Field", {"dt": "Role", "fieldname": "custom_enviro_role"})
	custom_field.in_standard_filter = 1
	custom_field.in_list_view = 1
	custom_field.save(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache(doctype="Role")
	print("Enviro Role field updated to be a Standard Filter and visible in List View.")


if __name__ == "__main__":
	run()
