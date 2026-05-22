import frappe


def execute():
	frappe.init(site="enviro.site")
	frappe.connect()
	dt = frappe.get_doc("DocType", "Enviro Team Folder")
	print(f"DocType: {dt.name}, Module: {dt.module}, Custom: {dt.custom}")


if __name__ == "__main__":
	execute()
