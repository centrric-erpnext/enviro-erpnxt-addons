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

	# 1. Register only the Master Block in the child table
	doc.custom_blocks = []
	master_block = "Enviro Unified Dashboard Master"
	doc.append("custom_blocks", {"custom_block_name": master_block, "label": "Main Dashboard"})

	# 2. Stable Single-Block Content
	content_blocks = [
		{
			"id": get_id(),
			"type": "custom_block",
			"data": {"custom_block_name": master_block, "col": 12},
		}
	]

	doc.content = json.dumps(content_blocks)
	doc.save()
	frappe.db.commit()
	print("Home Workspace updated with Master Unified Dashboard")


if __name__ == "__main__":
	update_home_workspace()
