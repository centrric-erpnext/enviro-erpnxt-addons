frappe.ui.form.on("Enviro Job", {
	refresh: function (frm) {
		// Fetch waste type if not already set on new records
		if (frm.is_new() && frm.doc.quotation && !frm.doc.custom_waste_type) {
			frm.trigger("quotation");
		}
	},
	quotation: function (frm) {
		if (frm.doc.quotation) {
			frappe.call({
				method: "enviro.enviro.api.invoice.get_quotation_waste_types",
				args: {
					quotation: frm.doc.quotation,
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("custom_waste_type", r.message);
					} else {
						frm.set_value("custom_waste_type", "");
					}
				},
			});
		} else {
			frm.set_value("custom_waste_type", "");
		}
	},
});
