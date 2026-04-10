import frappe


def execute():
	workspace_names = [
		"Home",
		"Sales",
		"Sites",
		"Team",
		"Scheduling",
		"Vehicles",
		"OH & S",
		"Intranet",
		"Accounts",
		"Enviro",
		"Invoice",
	]

	for name in workspace_names:
		if frappe.db.exists("Workspace", name):
			doc = frappe.get_doc("Workspace", name)
			print(
				f"[{name}] - Module: {doc.module} | Parent: {doc.get('parent_page', 'None')} | Seq: {doc.get('sequence_id', 0)} | Public: {doc.public} | Hidden: {doc.get('is_hidden', 0)}"
			)
		else:
			print(f"[{name}] - NOT FOUND!")

	print("\nListing all Workspaces currently in the Enviro module:")
	enviro_ws = frappe.get_all("Workspace", filters={"module": "Enviro"}, fields=["name"])
	for e in enviro_ws:
		print(f"- {e.name}")
