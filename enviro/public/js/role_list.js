frappe.listview_settings["Role"] = {
	onload: function (listview) {
		listview.page.add_action_item(__("Mark as Enviro Role"), function () {
			listview.call_bulk_action("enviro.api.sync_roles.set_enviro_role", {
				status: 1,
			});
		});
		listview.page.add_action_item(__("Unmark as Enviro Role"), function () {
			listview.call_bulk_action("enviro.api.sync_roles.set_enviro_role", {
				status: 0,
			});
		});
	},
};
