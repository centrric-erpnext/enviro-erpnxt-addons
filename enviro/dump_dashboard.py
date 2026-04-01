import frappe

def execute():
    doc = frappe.get_doc("Custom HTML Block", "Enviro Sales Dashboard")
    print(doc.script)
