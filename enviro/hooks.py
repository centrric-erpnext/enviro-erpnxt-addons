app_name = "enviro"
app_title = "Enviro"
app_publisher = "Centrric Innovations"
app_description = "Custom App for Enviro"
app_email = "support@centrric.com"
app_license = "mit"


fixtures = [
	"Role",
	"Custom Field",
	"Property Setter",
	"Client Script",
	"Server Script",
	"Custom HTML Block",
	"Warehouse Type",
	"Custom DocPerm",
]

# Apps
# ------------------
required_apps = ["erpnext"]

# App Include JS
# ------------------
app_include_js = "/assets/enviro/js/global_back_v4.js"

# DocType JS
# ------------------
doctype_list_js = {"Role": "public/js/role_list.js"}

# Document Events
# ---------------
doc_events = {
	"Quotation": {
		"before_save": "enviro.custom_scripts.quotation.before_save",
		"on_update": "enviro.custom_scripts.quotation.on_update",
	}
}

# Scheduled Tasks
# ---------------
scheduler_events = {"daily": ["enviro.cron.recurring.execute_daily_operations"]}

# Overriding Methods
# ------------------------------
override_doctype_dashboards = {"Vehicle": "enviro.custom_scripts.vehicle_dashboard.get_dashboard_data"}
