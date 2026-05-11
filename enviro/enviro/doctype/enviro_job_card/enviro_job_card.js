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
	refresh: function (frm) {
		// If it's a new record and quotation is already linked (e.g. via 'Create Job Card' button), fetch waste type
		if (frm.is_new() && frm.doc.source_quotation && !frm.doc.custom_waste_type) {
			frm.trigger("source_quotation");
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
			frappe.db
				.get_list("Quotation Item", {
					filters: { parent: frm.doc.source_quotation },
					fields: ["custom_waste_type"],
				})
				.then((data) => {
					if (data && data.length > 0) {
						let types = [
							...new Set(data.map((i) => i.custom_waste_type).filter(Boolean)),
						];
						frm.set_value("custom_waste_type", types.join(", "));
					} else {
						frm.set_value("custom_waste_type", "");
					}
				});
		} else {
			frm.set_value("custom_waste_type", "");
		}
	},
});
