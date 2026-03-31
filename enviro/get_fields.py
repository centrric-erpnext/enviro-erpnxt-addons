import frappe
def execute():
    meta = frappe.get_meta("Enviro Job Card")
    for d in meta.fields:
        print(f"{d.fieldname} ({d.fieldtype}) - {d.label}")
