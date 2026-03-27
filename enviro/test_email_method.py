import frappe
from enviro.custom_scripts.quotation import send_approval_email
import traceback

def execute():
    try:
        quote_name = "SAL-QTN-2026-00016"
        if frappe.db.exists("Quotation", quote_name):
            doc = frappe.get_doc("Quotation", quote_name)
            print(f"Quotation {quote_name} Analysis:")
            print(f"- Custom Site Link: {doc.custom_site}")
            print(f"- Custom Site Email: {doc.custom_site_email}")
            
            print("\nAttempting to call send_approval_email()...")
            # We wrap it in a try-catch to see the actual error
            result = send_approval_email(quote_name)
            print(f"Result: {result}")
        else:
            print(f"Quotation {quote_name} not found.")
    except Exception as e:
        print("\n--- ERROR DURING DISPATCH ---")
        print(traceback.format_exc())
