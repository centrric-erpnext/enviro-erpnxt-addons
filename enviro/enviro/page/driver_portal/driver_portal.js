frappe.pages["driver-portal"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Enviro Driver Portal"),
		single_column: true,
	});

	// Main container
	$(wrapper)
		.find(".layout-main-section")
		.empty()
		.append('<div class="driver-portal-container"></div>');

	const $container = $(wrapper).find(".driver-portal-container");

	// Initial render
	render_portal($container);
};

function render_portal($container) {
	// Loading state
	$container.html('<div class="empty-state">Loading your schedule...</div>');

	frappe.call({
		method: "enviro.api.mobile.get_driver_context",
		callback: (r) => {
			const context = r.message;
			render_header($container, context);

			if (!context.vpi_done) {
				render_vpi_alert($container);
			}

			fetch_and_render_jobs($container, context);
		},
	});
}

function render_header($container, context) {
	const header = `
		<div class="portal-header">
			<div>
				<h1 class="portal-title">Duty Roster</h1>
				<div class="driver-welcome">Good day, ${context.employee.employee_name}</div>
			</div>
			<div class="header-action">
				<button class="btn btn-sm btn-default" onclick="location.reload()">Refresh</button>
			</div>
		</div>
	`;
	$container.empty().append(header);
}

function render_vpi_alert($container) {
	const alert = `
		<div class="job-card-mobile" style="background: #fff1f2; border-color: #fecaca;">
			<div style="display:flex; gap:12px; align-items:center;">
				<div style="font-size:24px;">⚠️</div>
				<div>
					<div style="font-weight:700; color:#991b1b;">Safety Check Required</div>
					<div style="font-size:13px; color:#b91c1c;">Please submit your Vehicle Pre-Inspection before starting any jobs.</div>
				</div>
			</div>
			<button class="btn-mobile-primary" style="background:#dc2626; margin-top:15px;" onclick="open_vpi_form()">
				Start Safety Checklist
			</button>
		</div>
	`;
	$container.append(alert);
}

function fetch_and_render_jobs($container, context) {
	frappe.call({
		method: "enviro.api.mobile.get_assigned_jobs",
		callback: (r) => {
			const jobs = r.message || [];
			if (jobs.length === 0) {
				$container.append(
					'<div class="empty-state">You have no active assignments for today.</div>'
				);
				return;
			}

			jobs.forEach((job, index) => {
				const status_class = get_status_class(job.status);
				const time_label = job.scheduled_start_time
					? frappe.datetime.format_time(job.scheduled_start_time)
					: "All Day";

				const job_card = `
					<div class="job-card-mobile animate-in" style="animation-delay: ${index * 0.1}s">
						<div class="job-status-badge ${status_class}">${job.status}</div>
						<div class="job-customer">${job.customer}</div>
						<div class="job-site">
							<span>📍</span> ${job.site || "Unknown Site"}
						</div>
						<div style="font-size:13px; color:#64748b; margin-bottom:20px;">
							<b>Scheduled:</b> ${frappe.datetime.str_to_user(job.scheduled_start_date)} at ${time_label}
						</div>

						<div class="job-actions">
							${get_job_buttons(job, context.vpi_done)}
						</div>
					</div>
				`;
				$container.append(job_card);
			});
		},
	});
}

function get_status_class(status) {
	if (status === "Scheduled") return "status-scheduled";
	if (status === "In Transit") return "status-transit";
	if (status === "On Site") return "status-onsite";
	if (status === "Completed") return "status-completed";
	return "status-scheduled";
}

function get_job_buttons(job, vpi_done) {
	if (!vpi_done) {
		return `<button class="btn-mobile-primary btn-mobile-outline" disabled>Complete Safety Check First</button>`;
	}

	if (job.status === "Scheduled") {
		return `<button class="btn-mobile-primary" onclick="update_job('${job.name}', 'start')">🚀 Start Job</button>`;
	} else if (job.status === "In Transit") {
		return `<button class="btn-mobile-primary" style="background:#f59e0b;" onclick="update_job('${job.name}', 'arrive')">📍 Arrive on Site</button>`;
	} else if (job.status === "On Site") {
		return `<button class="btn-mobile-primary" style="background:#10b981;" onclick="update_job('${job.name}', 'complete')">✅ Complete Job</button>`;
	}
	return "";
}

window.update_job = function (job_name, action) {
	frappe.call({
		method: "enviro.api.mobile.update_job_status",
		args: { job_name: job_name, action: action },
		freeze: true,
		callback: (r) => {
			frappe.show_alert({ message: __("Status Updated!"), indicator: "green" });
			location.reload();
		},
	});
};

window.open_vpi_form = function () {
	frappe.new_doc("Vehicle Pre-Inspection Check");
};
