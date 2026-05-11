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
	source_quotation: function (frm) {
		if (frm.doc.source_quotation) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Quotation Item",
					filters: { parent: frm.doc.source_quotation },
					fields: ["custom_waste_type"],
				},
				callback: function (r) {
					if (r.message) {
						let types = [
							...new Set(r.message.map((i) => i.custom_waste_type).filter(Boolean)),
						];
						frm.set_value("custom_waste_type", types.join(", "));
					}
				},
			});
		} else {
			frm.set_value("custom_waste_type", "");
		}
	},
});
