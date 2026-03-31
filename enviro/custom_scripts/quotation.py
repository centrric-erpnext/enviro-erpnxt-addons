import frappe
from frappe.utils import get_url

def before_save(doc, method=None):
    # Enforce Enviro Job Card linkage
    if getattr(doc, "custom_accounts_approval_status", "") == "Approved":
        if not getattr(doc, "custom_enviro_job_card", None):
            frappe.throw("❌ You must create and link an <b>Enviro Job Card</b> before confirming this Quotation internally.")

    # If the user checks 'Requires Client Approval'
    if doc.custom_requires_client_approval:
        # Check if the client has already signed the web form or clicked the email button
        if doc.custom_customer_signature or doc.custom_client_approval_status == "Approved":
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
        
    if not getattr(doc, "custom_enviro_job_card", None):
        frappe.throw("❌ You must create and link an Enviro Job Card before sending the approval request to the customer.")
        
    # Generate a secure one-time token if one does not exist
    if not doc.custom_approval_token:
        doc.custom_approval_token = frappe.generate_hash(length=32)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    approve_link = f"{get_url()}/api/method/enviro.custom_scripts.quotation.handle_email_approval?name={doc.name}&token={doc.custom_approval_token}&action=approve"
    reject_link = f"{get_url()}/api/method/enviro.custom_scripts.quotation.handle_email_approval?name={doc.name}&token={doc.custom_approval_token}&action=reject"
    
    message = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 600px; padding: 25px; border: 1px solid #e5e7eb; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <h2 style="color: #111827; margin-top: 0;">Quotation Action Required</h2>
        <p style="color: #374151; font-size: 16px;">Dear {doc.customer_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Please review the attached quotation (<b>{doc.name}</b>). You can instantly approve or reject it by clicking one of the buttons below.</p>
        
        <div style="margin-top: 35px; margin-bottom: 35px;">
            <a href="{approve_link}" style="padding: 14px 28px; background-color: #10b981; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">✅ Approve Quotation</a>
            <a href="{reject_link}" style="padding: 14px 28px; background-color: #ef4444; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; margin-left: 15px;">❌ Reject Quotation</a>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin-bottom: 0;">Thank you,<br>Enviro Operations</p>
    </div>
    """
    
    frappe.sendmail(
        recipients=[doc.custom_site_email],
        subject=f"Action Required: Quotation {doc.name} Approval",
        message=message,
        reference_doctype="Quotation",
        reference_name=doc.name,
        attachments=[frappe.attach_print(doc.doctype, doc.name, file_name=f"Quotation_{doc.name}")],
        now=True
    )
    return "Sent"


@frappe.whitelist(allow_guest=True)
def handle_email_approval(name, token, action):
    try:
        if not frappe.db.exists("Quotation", name):
            
            html = """
            <div style='text-align: center; padding: 40px;'>
                <h1 style='color: #ef4444; font-size: 48px; margin-bottom: 10px;'>❌</h1>
                <h2>Document Not Found</h2>
                <p style='font-size: 18px; color: #374151;'>This quotation no longer exists in our system.</p>
            </div>
            """
            frappe.respond_as_web_page("Not Found", html, success=True)
            return
            
        doc = frappe.get_doc("Quotation", name)
        
        if not doc.custom_approval_token or doc.custom_approval_token != token:
            
            html = """
            <div style='text-align: center; padding: 40px;'>
                <h1 style='color: #fbbf24; font-size: 48px; margin-bottom: 10px;'>⚠️</h1>
                <h2>Link Already Used</h2>
                <p style='font-size: 18px; color: #374151;'>This quotation has already been approved or rejected.</p>
                <p style='color: #6b7280; font-size: 14px;'>Responses are final and cannot be changed.</p>
            </div>
            """
            frappe.respond_as_web_page("Already Responded", html, success=True)
            return
            
        if action == "approve":
            doc.custom_client_approval_status = "Approved"
            doc.custom_accounts_approval_status = "Pending" # Re-enable the Accounts step
            doc.custom_approval_token = "" # Invalidate token to prevent replay
            
            doc.save(ignore_permissions=True)
            # doc.submit() is REMOVED so Sales Team can review it as a Draft
            frappe.db.commit()
            
            html = f"""
            <div style='text-align: center; padding: 40px;'>
                <h1 style='color: #10b981; font-size: 48px; margin-bottom: 10px;'>✅</h1>
                <h2>Approval Successful</h2>
                <p style='font-size: 18px; color: #374151;'>Thank you! Quotation <b>{name}</b> is now fully approved.</p>
                <p style='color: #6b7280; font-size: 14px;'>You can safely close this window.</p>
            </div>
            """
            frappe.respond_as_web_page("Quotation Approved", html, success=True)
            return
            
        elif action == "reject":
            doc.custom_client_approval_status = "Rejected"
            doc.custom_approval_token = "" # Invalidate token
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            html = f"""
            <div style='text-align: center; padding: 40px;'>
                <h1 style='color: #ef4444; font-size: 48px; margin-bottom: 10px;'>🛑</h1>
                <h2>Quotation Rejected</h2>
                <p style='font-size: 18px; color: #374151;'>You have declined quotation <b>{name}</b>.</p>
                <p style='color: #6b7280; font-size: 14px;'>Our team will contact you shortly to review the details.</p>
            </div>
            """
            frappe.respond_as_web_page("Quotation Rejected", html, success=True)
            return
            
        frappe.respond_as_web_page("Invalid Action", "<p>The requested action is not supported.</p>", success=False, http_status_code=400)
        
    except Exception as e:
        frappe.respond_as_web_page("Server Error", f"<p>An error occurred: {str(e)}</p>", success=False, http_status_code=500)

@frappe.whitelist()
def submit_quotation(name):
    doc = frappe.get_doc("Quotation", name)
    doc.submit()
    return "Submitted"
