# Copyright (c) 2026, Centrric Innovations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EnviroJobCard(Document):
	def validate(self):
		self.fetch_waste_type()

	def fetch_waste_type(self):
		"""Aggregates all unique waste types from the linked quotation's items."""
		if self.source_quotation:
			# Use SQL to aggregate to handle multiple items efficiently
			waste_types = frappe.db.sql(
				"""
				SELECT DISTINCT custom_waste_type
				FROM `tabQuotation Item`
				WHERE parent = %s AND custom_waste_type IS NOT NULL AND custom_waste_type != ''
			""",
				self.source_quotation,
				pluck=True,
			)

			if waste_types:
				# Store as a sorted comma-separated string
				self.custom_waste_type = ", ".join(sorted(waste_types))
			else:
				self.custom_waste_type = ""

	def after_insert(self):
		# Automatically link this newly generated Job Card back into the Source Quotation
		if self.source_quotation:
			frappe.db.set_value("Quotation", self.source_quotation, "custom_enviro_job_card", self.name)
			# Instantly push a silent update to the user's browser so they don't get a Timestamp Mismatch error!
			frappe.publish_realtime("doc_update", {"doctype": "Quotation", "name": self.source_quotation})
