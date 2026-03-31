import frappe

def execute():
    # 1. Update Client Script for Resend and Pre-Dispatch Validation
    script_name = "Quotation Approval Dialog"
    doc = frappe.get_doc("Client Script", script_name)
    
    new_script = """
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        
        // Hide the checkbox entirely if the document is Submitted (1) or Cancelled (2)
        frm.set_df_property('custom_requires_client_approval', 'hidden', frm.doc.docstatus !== 0);

        // Infinite Resend Capability: Allow sending as long as it's Draft and NOT already Approved.
        if (frm.doc.docstatus === 0 && frm.doc.custom_requires_client_approval == 1 && frm.doc.custom_client_approval_status !== "Approved") {
            
            // Add a vibrant blue custom button explicitly for sending the email
            frm.add_custom_button(__('Send Site Approval Email'), function() {
                
                // Pre-Dispatch Validation 1: Site Email
                if (!frm.doc.custom_site_email) {
                    frappe.msgprint({title: 'Missing Site Email', message: 'You must link a Site that has a Site Email Address first!', indicator: 'red'});
                    return;
                }
                
                // Pre-Dispatch Validation 2: Job Card Linkage
                if (!frm.doc.custom_enviro_job_card) {
                    frappe.msgprint({title: 'Missing Job Card', message: 'You MUST create and link an Enviro Job Card before dispatching this email! Once the client signs, the Quotation will automatically submit and mathematically requires this card.', indicator: 'red'});
                    return;
                }
                
                // Call the backend email dispatcher
                frappe.call({
                    method: 'enviro.custom_scripts.quotation.send_approval_email',
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Dispatching Email securely...",
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({message: "Approval email precisely dispatched to the site manager!", indicator: 'green'});
                        }
                    }
                });
                
            }).addClass('btn-primary');
        }
    }
});
"""
    doc.script = new_script.strip()
    doc.save()
    
    # 2. Disable Conflicting Background Job Card generation
    if frappe.db.exists("Server Script", "Generate Driver Job Cards"):
        ss = frappe.get_doc("Server Script", "Generate Driver Job Cards")
        ss.disabled = 1
        ss.save()
        
    frappe.db.commit()
    print("Successfully updated Client Script and disabled conflicting Server Script!")
