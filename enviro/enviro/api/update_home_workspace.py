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

	# Correct structure for Frappe v15 Workspace Blocks
	# Type: custom_block, Data: custom_block_name
	blocks = [
		{
			"id": get_id(),
			"type": "header",
			"data": {"text": "Enviro Operations Center", "level": 2, "col": 12},
		},
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
	]

	doc.content = json.dumps(blocks)
	doc.save()
	frappe.db.commit()
	print("Home Workspace fixed with stable flat layout")


if __name__ == "__main__":
	update_home_workspace()
