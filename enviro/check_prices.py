import frappe

def execute():
    item_code = "Enviro Waste Service"
    print(f"Checking pricing for {item_code}...")
    
    # 1. Check Item record itself
    if frappe.db.exists("Item", item_code):
        item = frappe.get_doc("Item", item_code)
        print(f"Standard Rate on Item: {item.standard_rate}")
        print(f"Valuation Rate: {item.valuation_rate}")
    else:
        print("Item not found!")
        
    # 2. Check Item Price table
    prices = frappe.get_all("Item Price", filters={"item_code": item_code}, fields=["name", "price_list", "price_list_rate"])
    print(f"Item Prices: {prices}")
    
    # 3. Check for any Client Scripts or Server Scripts mentioning 500
    cs = frappe.get_all("Client Script", filters={'dt': 'Quotation'}, fields=["name", "script"])
    for c in cs:
        if "500" in (c.script or ""):
            print(f"Found '500' in Client Script: {c.name}")
            
    ss = frappe.get_all("Server Script", filters={'reference_doctype': 'Quotation'}, fields=["name", "script"])
    for s in ss:
        if "500" in (s.script or ""):
            print(f"Found '500' in Server Script: {s.name}")

