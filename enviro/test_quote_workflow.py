import frappe
from frappe.utils import today


def execute():
	print("--- STARTING QUOTATION WORKFLOW TEST ---")

	# 1. Create a mock Customer and Item if they don't exist
	if not frappe.db.exists("Customer", "Test Client"):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Test Client",
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", "Enviro Waste Service"):
		frappe.get_doc(
			{"doctype": "Item", "item_code": "Enviro Waste Service", "item_group": "Services"}
		).insert(ignore_permissions=True)

	# 2. Test Scenario A: Requires Client Approval
	print("\n--- TEST SCENARIO A: REQUIRES CLIENT APPROVAL ---")
	quote_a = frappe.new_doc("Quotation")
	quote_a.customer = "Test Client"
	quote_a.transaction_date = today()
	quote_a.append("items", {"item_code": "Enviro Waste Service", "qty": 1, "rate": 500})

	# Trigger the custom field
	quote_a.custom_requires_client_approval = 1
	quote_a.insert(ignore_permissions=True)

	print(f"1. Quote Created ({quote_a.name}) with Requires Client Approval = Checked")
	print("EXPECTED: Client = Pending, Accounts = (Empty)")
	print(
		f"ACTUAL:   Client = {quote_a.custom_client_approval_status}, Accounts = {quote_a.custom_accounts_approval_status}"
	)

	# Simulate the web form attaching a signature
	print("\n2. Client signs the Web Form portal...")
	quote_a.custom_customer_signature = "/private/files/test_signature.png"
	quote_a.save(ignore_permissions=True)

	print("EXPECTED: Client = Approved, Accounts = Pending")
	print(
		f"ACTUAL:   Client = {quote_a.custom_client_approval_status}, Accounts = {quote_a.custom_accounts_approval_status}"
	)

	# 3. Test Scenario B: Skips Client Approval
	print("\n--- TEST SCENARIO B: STRAIGHT TO ACCOUNTS ---")
	quote_b = frappe.new_doc("Quotation")
	quote_b.customer = "Test Client"
	quote_b.transaction_date = today()
	quote_b.append("items", {"item_code": "Enviro Waste Service", "qty": 1, "rate": 500})

	# Trigger the custom field
	quote_b.custom_requires_client_approval = 0
	quote_b.insert(ignore_permissions=True)

	print(f"1. Quote Created ({quote_b.name}) with Requires Client Approval = Unchecked")
	print("EXPECTED: Client = Not Required, Accounts = Pending")
	print(
		f"ACTUAL:   Client = {quote_b.custom_client_approval_status}, Accounts = {quote_b.custom_accounts_approval_status}"
	)

	print("\n--- WORKFLOW TEST COMPLETE ---")
