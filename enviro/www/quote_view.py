import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.title = _("Quotation Review")
	context.no_cache = 1

	name = frappe.form_dict.get("name")
	token = frappe.form_dict.get("token")

	if not name or not token:
		context.error_title = _("Invalid Request")
		context.error_message = _("The link is missing quotation details.")
		return context

	if not frappe.db.exists("Quotation", name):
		context.error_title = _("Document Not Found")
		context.error_message = _("This quotation no longer exists in our system.")
		return context

	doc = frappe.get_doc("Quotation", name)

	if not doc.custom_approval_token or doc.custom_approval_token != token:
		context.error_title = _("Link Already Used")
		context.error_message = _(
			"This quotation has already been approved, rejected, or the token is invalid. Responses are final and cannot be changed."
		)
		return context

	context.doc = doc

	# Fetch site details
	context.site = None
	if doc.custom_site:
		context.site = frappe.get_doc("Site", doc.custom_site)

	context.items = doc.items
	context.doc_date = doc.transaction_date.strftime("%d/%m/%Y") if doc.transaction_date else ""

	return context
