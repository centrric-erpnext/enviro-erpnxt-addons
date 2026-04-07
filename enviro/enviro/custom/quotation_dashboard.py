from frappe import _

def get_data(data=None):
    if not data:
        try:
            from erpnext.selling.doctype.quotation.quotation_dashboard import get_data as std_data
            data = std_data()
        except ImportError:
            data = {"fieldname": "source_quotation", "transactions": []}
            
    # Inject our Operations Docs
    data.setdefault("transactions", []).append({
        "label": _("Enviro Operations"),
        "items": ["Enviro Job Card", "Enviro Job"]
    })
    
    return data
