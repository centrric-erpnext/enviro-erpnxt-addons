import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.title = _("Quotation Review")
	context.no_cache = 1

	name = frappe.form_dict.get("name")
	token = frappe.form_dict.get("token")

	preview = frappe.form_dict.get("preview")

	if not name or (not token and not preview):
		context.error_title = _("Invalid Request")
		context.error_message = _("The link is missing quotation details.")
		return context

	if not frappe.db.exists("Quotation", name):
		context.error_title = _("Document Not Found")
		context.error_message = _("This quotation no longer exists in our system.")
		return context

	doc = frappe.get_doc("Quotation", name)

	if not preview:
		if not doc.custom_approval_token or doc.custom_approval_token != token:
			context.error_title = _("Link Already Used")
			context.error_message = _(
				"This quotation has already been approved, rejected, or the token is invalid. Responses are final and cannot be changed."
			)
			return context
	elif frappe.session.user == "Guest":
		context.error_title = _("Unauthorized")
		context.error_message = _("You must be logged in to preview this quotation.")
		return context
	else:
		# In preview mode, ensure UI shows 'Preview Mode' instead of interactive buttons
		context.is_preview = True

	context.doc = doc

	# Fetch site details
	context.site = None
	if doc.custom_site:
		context.site = frappe.get_doc("Site", doc.custom_site)

	context.items = doc.items
	context.doc_date = doc.transaction_date.strftime("%d/%m/%Y") if doc.transaction_date else ""

	return context
