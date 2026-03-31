# Copyright (c) 2026, Centrric Innovations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EnviroJobCard(Document):
    def after_insert(self):
        # Automatically link this newly generated Job Card back into the Source Quotation
        if self.source_quotation:
            frappe.db.set_value("Quotation", self.source_quotation, "custom_enviro_job_card", self.name)
