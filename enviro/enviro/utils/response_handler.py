import json

import frappe


class ResponseHandler:
	@staticmethod
	def success(data):
		"""
		Sets the Frappe response for a successful API call (200 OK).
		Wraps the output in a {"data": ...} structure.
		"""
		frappe.response["http_status_code"] = 200
		frappe.response["data"] = data

	@staticmethod
	def error(status_code, message, title="Error"):
		"""
		Sets the Frappe response for a controlled API error.
		- status_code: The HTTP status code (e.g., 400 Bad Request, 409 Conflict).
		- message: The error message to be shown in the UI.
		- title: The title for the error message popup in the UI.
		"""
		# Build the user-facing error structure that Frappe's UI understands
		error_payload = [
			{
				"message": str(message),  # Ensure message is a string
				"title": title,
				"indicator": "red",
			}
		]

		frappe.response["http_status_code"] = status_code
		frappe.response["_server_messages"] = json.dumps(error_payload)
