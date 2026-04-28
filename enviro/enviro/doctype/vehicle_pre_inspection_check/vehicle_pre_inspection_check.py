import frappe
from frappe.model.document import Document


class VehiclePreInspectionCheck(Document):
	def on_submit(self):
		# If conducted_check is not checked, it implies something is wrong
		# Or if fault details are entered
		if self.any_fault_to_report:
			frappe.msgprint(
				msg=f"Warning: Vehicle {self.vehicle} has reported faults.",
				title="Faults Reported",
				indicator="red",
				alert=True,
			)
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"description": f"URGENT: Vehicle {self.vehicle} reported faults on {self.date} by {self.driver}.",
					"reference_type": "Vehicle Pre-Inspection Check",
					"reference_name": self.name,
					"assigned_by": self.driver,
				}
			).insert(ignore_permissions=True)
