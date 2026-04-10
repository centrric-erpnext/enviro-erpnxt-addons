from datetime import timedelta

import frappe
from frappe.model.document import Document


class EnviroWeeklyTimesheet(Document):
	def validate(self):
		for row in self.get("timesheet_table"):
			if row.start and row.finish:

				def get_seconds(t):
					if isinstance(t, timedelta):
						return t.total_seconds()

					parts = str(t).split(":")
					h = int(parts[0]) if len(parts) > 0 else 0
					m = int(parts[1]) if len(parts) > 1 else 0

					# FIXED LINE: Convert to float first to safely strip microseconds
					s = int(float(parts[2])) if len(parts) > 2 else 0

					return h * 3600 + m * 60 + s

				diff = (get_seconds(row.finish) - get_seconds(row.start)) / 3600.0
				row.total_hours = round(diff, 2) if diff > 0 else 0
