def get_dashboard_data(data):
	if "transactions" not in data:
		data["transactions"] = []

	data["transactions"].append(
		{
			"label": "Enviro Safety Checks",
			"items": ["Vehicle Pre-Inspection Check"],
		}
	)

	return data
