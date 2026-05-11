// Copyright (c) 2026, Centrric Innovations and contributors
// For license information, please see license.txt

frappe.ui.form.on("Enviro Job Card", {
	setup: function (frm) {
		frm.set_query("sales_person", function () {
			return {
				query: "enviro.enviro.api.user_utils.get_sales_employees",
			};
		});
	},
	onload: function (frm) {
		if (frm.is_new() && !frm.doc.sales_person) {
			frappe.call({
				method: "enviro.enviro.api.user_utils.get_current_employee",
				callback: function (r) {
					if (r.message) {
						frm.set_value("sales_person", r.message);
					}
				},
			});
		}
	},
	site: function (frm) {
		if (frm.doc.site) {
			frappe.db.get_value("Site", frm.doc.site, "industry_type", (r) => {
				if (r && r.industry_type) {
					frm.set_value("industry_type", r.industry_type);
				}
			});
		}
	},
});
