import frappe

def before_save(doc, method=None):
    # If the user checks 'Requires Client Approval'
    if doc.custom_requires_client_approval:
        # Check if the client has already signed the web form
        if doc.custom_customer_signature:
            # Client has signed it!
            doc.custom_client_approval_status = "Approved"
            
            # Now it proceeds to the Accounts Review stage (if not already approved)
            if doc.custom_accounts_approval_status not in ["Approved", "Rejected"]:
                doc.custom_accounts_approval_status = "Pending"
                
        else:
            # Client hasn't signed it yet
            doc.custom_client_approval_status = "Pending"
            # Explicitly blank out the accounts status so they know it's not ready for them
            doc.custom_accounts_approval_status = ""
            
    # If the user DOES NOT require client approval
    else:
        doc.custom_client_approval_status = "Not Required"
        
        # It goes straight to the Accounts Review stage
        if doc.custom_accounts_approval_status not in ["Approved", "Rejected"]:
            doc.custom_accounts_approval_status = "Pending"

@frappe.whitelist()
def send_approval_email(docname):
    doc = frappe.get_doc("Quotation", docname)
    
    if not doc.custom_site_email:
        frappe.throw("No Site Email found to send the approval request.")
        
    message = f"""
    <h3>Quotation Details</h3>
    <p>Dear {doc.customer_name},</p>
    <p>Please review and approve the attached quotation ({doc.name}).</p>
    <p>You can view and digitally sign the quotation by clicking the button below:</p>
    <br>
    <a href="/approve-quote?name={doc.name}" style="padding: 10px 20px; background-color: #0ea5e9; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Review & Approve Quotation</a>
    <br><br>
    <p>Thank you,</p>
    """
    
    frappe.sendmail(
        recipients=[doc.custom_site_email],
        subject=f"Action Required: Quotation {doc.name} Approval",
        message=message,
        reference_doctype="Quotation",
        reference_name=doc.name
    )
    return "Sent"

