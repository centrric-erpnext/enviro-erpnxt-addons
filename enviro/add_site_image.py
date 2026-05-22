import frappe


def execute():
	frappe.init(site="enviro.site")
	frappe.connect()
	if not frappe.db.exists("Custom Field", {"dt": "Site", "fieldname": "custom_site_image"}):
		custom_field = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Site",
				"fieldname": "custom_site_image",
				"label": "Site Image",
				"fieldtype": "Attach Image",
				"insert_after": "site_name",
			}
		)
		custom_field.insert(ignore_permissions=True)
		frappe.db.commit()
		print("Site Image Custom Field created successfully.")
	else:
		print("Custom Field 'custom_site_image' already exists.")


if __name__ == "__main__":
	execute()
