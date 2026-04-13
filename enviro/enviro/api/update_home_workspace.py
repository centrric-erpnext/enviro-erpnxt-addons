import json

import frappe


def update_home_workspace():
	if not frappe.db.exists("Workspace", "Home"):
		print("Home Workspace not found")
		return

	import random
	import string

	def get_id():
		return "".join(random.choices(string.ascii_letters + string.digits, k=10))

	doc = frappe.get_doc("Workspace", "Home")

	# 1. Populate custom_blocks child table (Required for v15 visibility)
	doc.custom_blocks = []
	block_names = [
		"Enviro Home Notifications",
		"Enviro Home Job List",
		"Enviro Home Weather",
		"Enviro Home Schedule Grid",
	]
	for name in block_names:
		doc.append("custom_blocks", {"custom_block_name": name, "label": name})

	# 2. Define the rich 2-column layout in content JSON
	# Using the 'columns' block structure for v15
	content_blocks = [
		{
			"id": get_id(),
			"type": "header",
			"data": {"text": '<span class="h4">Enviro Operations Center</span>', "level": 2, "col": 12},
		},
		{
			"id": get_id(),
			"type": "columns",
			"data": {
				"content": [
					{
						"col": 8,
						"blocks": [
							{
								"id": get_id(),
								"type": "custom_block",
								"data": {"custom_block_name": "Enviro Home Notifications", "col": 12},
							},
							{
								"id": get_id(),
								"type": "custom_block",
								"data": {"custom_block_name": "Enviro Home Job List", "col": 12},
							},
						],
					},
					{
						"col": 4,
						"blocks": [
							{
								"id": get_id(),
								"type": "custom_block",
								"data": {"custom_block_name": "Enviro Home Weather", "col": 12},
							},
							{
								"id": get_id(),
								"type": "custom_block",
								"data": {"custom_block_name": "Enviro Home Schedule Grid", "col": 12},
							},
						],
					},
				]
			},
		},
	]

	doc.content = json.dumps(content_blocks)
	doc.save()
	frappe.db.commit()
	print("Home Workspace restored to 2-column layout with child table registration")


if __name__ == "__main__":
	update_home_workspace()
