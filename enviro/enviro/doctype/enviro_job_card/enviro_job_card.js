// Copyright (c) 2026, Centrric Innovations and contributors
// For license information, please see license.txt

frappe.ui.form.on("Enviro Job Card", {
	setup: function (frm) {
		frm.is_new_job_card = frm.is_new();
	},
	onload: function (frm) {
		if (frm.is_new() && !frm.doc.sales_person) {
			frappe.call({
				method: "enviro.api.user_utils.get_current_employee",
				callback: function (r) {
					if (r.message) {
						let emp_name = typeof r.message === "object" ? r.message.name : r.message;
						frm.set_value("sales_person", emp_name);
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

		if (!frm.is_new() && frm.doc.source_quotation) {
			// Check if the linked quotation requires approval and is not approved yet
			frappe.db.get_value(
				"Quotation",
				frm.doc.source_quotation,
				["custom_client_approval_status", "docstatus"],
				(r) => {
					if (r && r.custom_client_approval_status !== "Approved" && r.docstatus === 0) {
						frm.add_custom_button(__("Send Site Approval Email"), function () {
							frm.trigger("send_site_approval_email");
						}).addClass("btn-primary");
					}
				}
			);
		}
	},
	after_save: function (frm) {
		if (frm.is_new_job_card && frm.doc.source_quotation) {
			frm.is_new_job_card = false; // Reset the flag

			// Check if the linked quotation requires approval and is not approved yet
			frappe.db.get_value(
				"Quotation",
				frm.doc.source_quotation,
				["custom_client_approval_status", "docstatus"],
				(r) => {
					if (r && r.custom_client_approval_status !== "Approved" && r.docstatus === 0) {
						frappe.confirm(
							__(
								"Job Card created. Do you want to send the Site Approval Email now?"
							),
							() => {
								frm.trigger("send_site_approval_email");
							}
						);
					}
				}
			);
		}
	},
	send_site_approval_email: function (frm) {
		if (!frm.doc.site_contact_email) {
			frappe.msgprint({
				title: "Missing Site Email",
				message: "You must provide a Site Contact Email first!",
				indicator: "red",
			});
			return;
		}

		let d = new frappe.ui.Dialog({
			title: "Preview Client Quotation",
			fields: [
				{
					fieldname: "preview_html",
					fieldtype: "HTML",
					options: `<div style="width: 100%; height: 80vh; overflow: hidden; border: 1px solid #d1d5db; border-radius: 8px;">
						<iframe src="/quote_view?name=${frm.doc.source_quotation}&preview=1" style="width: 100%; height: 100%; border: none;"></iframe>
					</div>`,
				},
			],
			size: "extra-large",
			primary_action_label: "Approve & Continue to Send",
			primary_action: function () {
				d.hide();
				frappe.prompt(
					[
						{
							label: "CC",
							fieldname: "cc",
							fieldtype: "Data",
							description: "Comma separated email addresses",
						},
						{
							label: "BCC",
							fieldname: "bcc",
							fieldtype: "Data",
							description: "Comma separated email addresses",
						},
						{
							label: "Mail Body (Optional)",
							fieldname: "custom_message",
							fieldtype: "Text",
							description: "Add a custom message to the client",
						},
					],
					function (values) {
						frappe.call({
							method: "enviro.custom_scripts.quotation.send_approval_email",
							args: {
								docname: frm.doc.source_quotation,
								cc: values.cc,
								bcc: values.bcc,
								custom_message: values.custom_message,
							},
							freeze: true,
							freeze_message: "Dispatching Email securely...",
							callback: function (res) {
								if (!res.exc) {
									frappe.show_alert({
										message:
											"Approval email precisely dispatched to the site manager!",
										indicator: "green",
									});
								}
							},
						});
					},
					"Email Options",
					"Send Email"
				);
			},
		});
		d.show();
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
				method: "enviro.api.invoice.get_quotation_waste_types",
				args: {
					quotation: frm.doc.source_quotation,
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
