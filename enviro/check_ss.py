import frappe

def execute():
    try:
        ss = frappe.get_doc("Selling Settings")
        print(f"Selling Settings - Auto insert: {ss.get('auto_insert_price_list_rate_if_missing')}")
    except Exception as e:
        print(f"Error checking selling settings: {e}")
