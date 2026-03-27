
        <h3>Quotation Details</h3>
        <p>Dear {{ doc.customer_name }},</p>
        <p>Please review and approve the attached quotation ({{ doc.name }}).</p>
        <p>You can view and digitally sign the quotation by clicking the button below:</p>
        <br>
        <a href="/approve-quote?name={{ doc.name }}" style="padding: 10px 20px; background-color: #0ea5e9; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Review & Approve Quotation</a>
        <br><br>
        <p>Thank you,</p>
        <p>{{ frappe.session.user }}</p>
        