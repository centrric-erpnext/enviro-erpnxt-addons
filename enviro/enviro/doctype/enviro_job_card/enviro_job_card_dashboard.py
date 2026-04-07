from frappe import _

def get_data():
    return {
        "fieldname": "source_job_card",
        "transactions": [
            {
                "label": _("Job Executions"),
                "items": ["Enviro Job"]
            }
        ]
    }
