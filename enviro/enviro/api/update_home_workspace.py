import json

import frappe


def update_home_workspace():
	if not frappe.db.exists("Workspace", "Home"):
		print("Home Workspace not found")
		return

	doc = frappe.get_doc("Workspace", "Home")

	# Define the new blocks
	# Note: In Frappe v15, Workspace uses 'content' which is a JSON string of blocks
	blocks = [
		{"type": "header", "data": {"text": "Enviro Operations Center", "level": 2}},
		{"type": "spacer", "data": {"height": "20px"}},
		{
			"type": "columns",
			"data": {
				"columns": [
					{
						"width": "66%",
						"blocks": [
							{"type": "custom_html", "data": {"html_block": "Enviro Home Notifications"}},
							{"type": "custom_html", "data": {"html_block": "Enviro Home Job List"}},
						],
					},
					{
						"width": "33%",
						"blocks": [
							{"type": "custom_html", "data": {"html_block": "Enviro Home Weather"}},
							{"type": "custom_html", "data": {"html_block": "Enviro Home Schedule Grid"}},
						],
					},
				]
			},
		},
	]

	# Standard Frappe v15 structure for cards/charts can be added too,
	# but we will focus on these custom components as requested.

	# We will prepend these to any existing content if possible or just replace if requested
	# For this professional implementation, we will replace the 'content' field
	doc.content = json.dumps(blocks)
	doc.save()
	frappe.db.commit()
	print("Home Workspace updated successfully")


if __name__ == "__main__":
	update_home_workspace()
