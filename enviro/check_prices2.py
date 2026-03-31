import frappe

def execute():
    item_code = "Enviro Waste Service"
    prices = frappe.get_all("Item Price", filters={"item_code": item_code}, fields=["name", "price_list", "price_list_rate"])
    
    if prices:
        print(f"Still found {len(prices)} Item Price records!")
        for p in prices:
            print(f"- {p.name}: {p.price_list_rate}")
            # Delete it unconditionally to help the user
            frappe.delete_doc("Item Price", p.name)
            print(f"  -> DELETED {p.name}")
        frappe.db.commit()
    else:
        print("No Item Price records found! It must be coming from somewhere else or a cached old document.")
