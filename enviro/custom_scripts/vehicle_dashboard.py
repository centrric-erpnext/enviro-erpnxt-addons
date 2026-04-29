def get_dashboard_data(data):
	if "transactions" not in data:
		data["transactions"] = []

	data["transactions"].append(
		{
			"label": "Enviro Safety Checks",
			"items": ["Vehicle Pre-Inspection Check"],
		}
	)

	if "non_standard_fieldnames" not in data:
		data["non_standard_fieldnames"] = {}

	data["non_standard_fieldnames"]["Vehicle Pre-Inspection Check"] = "vehicle"

	return data
