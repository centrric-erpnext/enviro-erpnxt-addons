import frappe
from frappe.model.document import Document


class VehiclePreStartChecklist(Document):
	def on_submit(self):
		if self.overall_status == "Unsafe - Do Not Drive":
			frappe.msgprint(
				msg=f"Warning: Vehicle {self.vehicle} reported as Unsafe.",
				title="Unsafe Vehicle",
				indicator="red",
				alert=True
			)
			frappe.get_doc({
				"doctype": "ToDo",
				"description": f"URGENT: Vehicle {self.vehicle} reported as Unsafe on {self.date} by driver {self.driver}.",
				"reference_type": "Vehicle Pre-Start Checklist",
				"reference_name": self.name,
				"owner": frappe.session.user
			}).insert(ignore_permissions=True)
