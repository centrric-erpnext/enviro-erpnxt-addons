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

