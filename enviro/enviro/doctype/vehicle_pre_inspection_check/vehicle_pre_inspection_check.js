frappe.ui.form.on("Vehicle Pre-Inspection Check", {
	refresh(frm) {
		// Custom CSS to create the 4-column layout for the checklist
		let style = `
			<style>
				/* Target the checklist section */
				div[data-fieldname="sec_checklist_header"] + .section-body {
					display: flex !important;
					flex-wrap: wrap !important;
					gap: 10px !important;
				}

				div[data-fieldname="sec_checklist_header"] + .section-body .form-column {
					flex: 1 1 23% !important;
					min-width: 200px !important;
					border: 1px solid #f1f5f9;
					padding: 10px;
					border-radius: 8px;
					background: #fafafa;
				}

				/* Styling the labels to look like the checklist */
				.control-label {
					font-weight: 600 !important;
					color: #475569 !important;
				}

				/* Color indicator for Select fields */
				select.input-with-feedback[data-fieldname$="level"],
				select.input-with-feedback[data-fieldname$="system"],
				select.input-with-feedback[data-fieldname$="check"],
				select.input-with-feedback[data-fieldname$="status"] {
					font-weight: bold;
				}

				option[value="Pass"] { color: green; }
				option[value="Fail"] { color: red; }
			</style>
		`;

		// Inject style
		if (!document.getElementById("checklist-replica-style")) {
			$('<div id="checklist-replica-style">').html(style).appendTo("head");
		}

		// Make signature field a bit larger
		frm.get_field("driver_signature").$wrapper.css("min-height", "150px");
	},

	validate(frm) {
		// Ensure signature is provided if submitting
		if (frm.doc.docstatus === 1 && !frm.doc.driver_signature) {
			frappe.msgprint(__("Please provide Driver Signature before submitting."));
			frappe.validated = false;
		}
	},
});
