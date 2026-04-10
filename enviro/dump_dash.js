/* eslint-disable */
const styles = `
<style>
/* Layout defaults */
.sched-wrapper { display: flex; height: calc(100vh - 140px); gap: 20px; font-family: Inter, sans-serif; background: #f2f5f8; padding: 10px; }
.sched-left { width: 45%; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden;}
.sched-right { width: 55%; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }

/* Left Panel Queue */
.queue-header { padding: 15px; border-bottom: 1px solid #eef1f4; font-weight: bold; background: #fff; display: flex; gap: 10px;}
.queue-table-wrapper { flex: 1; overflow-y: auto; padding: 10px; }
.queue-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 12px; }
.queue-table th { padding: 8px; border-bottom: 2px solid #eef1f4; position: sticky; top: 0; background: white; z-index: 10; color: #555; }
.queue-table td { padding: 10px 8px; border-bottom: 1px solid #f1f5f9; }
.job-pill { background: #f8fafc; border: 1px solid #e2e8f0; padding: 4px 8px; border-radius: 6px; font-weight: bold; color: #475569; display: inline-block; cursor: pointer; }
.job-pill:hover { filter: brightness(0.95); }
.btn-schedule { background: #10b981; color: white; border: none; padding: 5px 12px; border-radius: 12px; font-size: 11px; font-weight: bold; cursor: pointer; }
.btn-schedule:hover { background: #059669; }

/* Right Panel Matrix */
.matrix-header-container { display: flex; overflow: hidden; background: #f8fafc; border-bottom: 1px solid #e2e8f0; flex-shrink: 0;}
.matrix-row-labels-header { width: 100px; padding: 12px; background: #f1f5f9; font-weight: bold; font-size: 12px; text-align: center; border-right: 1px solid #e2e8f0; flex-shrink: 0; }
.matrix-columns-wrapper { display: flex; flex: 1; overflow-x: auto; }
.matrix-col-header { flex: 1; min-width: 140px; padding: 12px; background: #f1f5f9; text-align: center; font-size: 12px; font-weight: bold; border-right: 1px solid #e2e8f0; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #475569; border-top: 4px solid #0ea5e9;}

.matrix-body-container { flex: 1; display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden; }
.matrix-row { display: flex; min-height: 100px; border-bottom: 1px solid #e2e8f0; }
.matrix-row-label { width: 100px; padding: 10px; border-right: 1px solid #e2e8f0; font-size: 11px; text-align: center; background: #fff; font-weight: bold; flex-shrink: 0; display:flex; flex-direction:column; justify-content:center;}
.matrix-cells-wrapper { display: flex; flex: 1; overflow-x: auto;}
.matrix-cell { flex: 1; min-width: 140px; border-right: 1px solid #e2e8f0; position: relative; padding: 5px; background: #f8fafc; transition: 0.2s; display:flex; flex-direction:column; align-items:center; justify-content:flex-start;}
.matrix-cell:hover { background: #f1f5f9; }

/* Scheduled Event Card inside cell */
.sched-event { background: #bae6fd; border: 1px solid #38bdf8; border-radius: 6px; padding: 6px; font-size: 10px; text-align: center; color: #0369a1; font-weight: bold; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 4px; cursor: pointer; width: 95%;}
.sched-event .ev-title { font-size: 12px; color: #1e293b; margin-bottom: 2px; background: rgba(255,255,255,0.8); border-radius: 4px; padding: 2px;}
.sched-event .ev-status { background: #ffedd5; color: #c2410c; padding: 2px 8px; border-radius: 10px; display: inline-block; margin-top: 4px; font-size:9px;}
</style>
`;

let state = {
	jobs: [],
	vehicles: [],
	dates: [],
};

// Generate next 7 days statically
let today = new Date();
for (let i = 0; i < 7; i++) {
	let d = new Date(today);
	d.setDate(today.getDate() + i);
	state.dates.push(d);
}

function render() {
	let html = styles + `<div class="sched-wrapper">`;

	// LEFT PANEL (Queue)
	html += `<div class="sched-left">
        <div class="queue-header">
            <div style="background:#0ea5e9; color:white; padding:4px 16px; border-radius:20px; font-size:13px;">Unscheduled Approvals</div>
        </div>
        <div class="queue-table-wrapper">
            <table class="queue-table">
                <thead><tr><th>Job</th><th>Client</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
   `;
	let unscheduled = state.jobs.filter((j) => !j.scheduled_start_date);

	if (unscheduled.length === 0)
		html += `<tr><td colspan="4" style="text-align:center; padding: 30px; color:#888;">All authorized jobs have been scheduled.</td></tr>`;

	unscheduled.forEach((j) => {
		html += `
           <tr>
               <td><span class="job-pill" onclick="frappe.set_route('Form', 'Enviro Job Card', '${
					j.name
				}')">${j.name}</span></td>
               <td style="font-weight:bold; color:#0f172a;">${j.customer || "N/A"}</td>
               <td><span style="background:#dcfce7; color:#166534; padding:2px 6px; border-radius:10px; font-size:9px; font-weight:bold;">Approved</span></td>
               <td><button class="btn-schedule" onclick="window.ph2_modal('${
					j.name
				}')">Schedule</button></td>
           </tr>
       `;
	});

	html += `</tbody></table></div></div>`;

	// RIGHT PANEL (Matrix Grid)
	html += `<div class="sched-right">`;
	html += `<div class="matrix-header-container">
      <div class="matrix-row-labels-header">Timeline</div>
      <div class="matrix-columns-wrapper" id="matrix-col-scroll">
   `;

	if (state.vehicles.length === 0) html += `<div style="padding:10px;">No Vehicles found.</div>`;

	state.vehicles.forEach((v) => {
		html += `<div class="matrix-col-header">${v.license_plate || v.name}</div>`;
	});
	html += `</div></div>`;

	html += `<div class="matrix-body-container">`;

	state.dates.forEach((d) => {
		let dStr = frappe.datetime.obj_to_str(d);

		html += `<div class="matrix-row">
           <div class="matrix-row-label">
              <span style="color:#64748b; font-size: 10px;">${d.toLocaleDateString("en-AU", {
					weekday: "long",
				})}</span>
              <span style="color:#0f172a; font-size: 12px;">${frappe.datetime.str_to_user(
					dStr
				)}</span>
           </div>
           <div class="matrix-cells-wrapper sync-scroll">
       `;

		state.vehicles.forEach((v) => {
			let vJobs = state.jobs.filter(
				(j) => j.scheduled_start_date === dStr && j.vehicle === v.name
			);

			html += `<div class="matrix-cell">`;
			vJobs.forEach((vj) => {
				html += `<div class="sched-event" onclick="frappe.set_route('Form', 'Enviro Job Card', '${
					vj.name
				}')">
                   <div class="ev-title">${vj.name}</div>
                   <div>${vj.driver || "Driver Pending"}</div>
                   <div class="ev-status">Allocated</div>
               </div>`;
			});

			if (vJobs.length === 0) {
				html += `<div style="color:#cbd5e1; font-size:10px; margin-top:30px;">+</div>`;
			}
			html += `</div>`;
		});

		html += `</div></div>`;
	});

	html += `</div></div></div>`;

	root_element.innerHTML = html;

	// Sync scroll
	let headerScroll = root_element.querySelector("#matrix-col-scroll");
	if (headerScroll) {
		root_element.querySelectorAll(".sync-scroll").forEach((row) => {
			row.addEventListener("scroll", function (e) {
				headerScroll.scrollLeft = e.target.scrollLeft;
				root_element.querySelectorAll(".sync-scroll").forEach((other) => {
					if (other !== e.target) other.scrollLeft = e.target.scrollLeft;
				});
			});
		});
	}
}

window.ph2_modal = function (job_id) {
	let d = new frappe.ui.Dialog({
		title: "Schedule Assignment: " + job_id,
		fields: [
			{
				label: "Scheduled Start Date",
				fieldname: "scheduled_start_date",
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.get_today(),
			},
			{
				label: "Scheduled Start Time",
				fieldname: "scheduled_start_time",
				fieldtype: "Time",
				reqd: 1,
				default: frappe.datetime.now_time(),
			},
			{ fieldtype: "Column Break" },
			{
				label: "Scheduled End Date",
				fieldname: "scheduled_end_date",
				fieldtype: "Date",
				default: frappe.datetime.get_today(),
			},
			{
				label: "Scheduled End Time",
				fieldname: "scheduled_end_time",
				fieldtype: "Time",
			},
			{ fieldtype: "Section Break", label: "Resource Allocation" },
			{
				label: "Assign Truck",
				fieldname: "vehicle",
				fieldtype: "Link",
				options: "Vehicle",
				reqd: 1,
			},
			{
				label: "Primary Driver",
				fieldname: "driver",
				fieldtype: "Link",
				options: "Employee",
				reqd: 1,
			},
			{ fieldtype: "Section Break", label: "Additional Team" },
			{
				label: "Additional Support Team",
				fieldname: "team_members",
				fieldtype: "Table MultiSelect",
				options: "Enviro Job Team Member",
				description: "Search and link additional staff to ride alongside the driver.",
			},
		],
		size: "large",
		primary_action_label: "Schedule Job",
		primary_action(values) {
			frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "Enviro Job Card",
					name: job_id,
					fieldname: {
						scheduled_start_date: values.scheduled_start_date,
						scheduled_start_time: values.scheduled_start_time,
						scheduled_end_date: values.scheduled_end_date,
						scheduled_end_time: values.scheduled_end_time,
						vehicle: values.vehicle,
						driver: values.driver,
						status: "Assigned",
						team_members: values.team_members || [],
					},
				},
				freeze: true,
				freeze_message: "Allocating Vehicles securely...",
				callback: function (r) {
					if (!r.exc) {
						frappe.show_alert({
							message: "Job Scheduled and pushed to Matrix!",
							indicator: "green",
						});
						d.hide();
						fetch_data(); // Automatically re-draws the calendar grid!
					}
				},
			});
		},
	});

	// Auto-fetch existing data if the job was already partially setup
	frappe.db.get_doc("Enviro Job Card", job_id).then((doc) => {
		d.set_values({
			scheduled_start_date: doc.scheduled_start_date || frappe.datetime.get_today(),
			scheduled_start_time: doc.scheduled_start_time || frappe.datetime.now_time(),
			scheduled_end_date: doc.scheduled_end_date || frappe.datetime.get_today(),
			scheduled_end_time: doc.scheduled_end_time,
			vehicle: doc.vehicle,
			driver: doc.driver,
			team_members: doc.team_members,
		});
	});

	d.show();
};

function fetch_data() {
	root_element.innerHTML = `<div style="padding: 40px; text-align:center; color: #888;">Fetching Secure Analytics from Approved Quotations...</div>`;
	frappe.call({
		method: "enviro.enviro.api.scheduling.get_scheduling_data",
		callback: function (r) {
			if (r.message) {
				state.jobs = r.message.jobs || [];
				state.vehicles = r.message.vehicles || [];
			}
			render();
		},
	});
}
fetch_data();
