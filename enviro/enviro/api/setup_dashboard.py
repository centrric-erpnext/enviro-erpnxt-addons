import frappe


@frappe.whitelist()
def run_setup():
	# 1. Notification Section
	create_block(
		name="Enviro Home Notifications",
		html="""
        <div id="enviro-notifications" class="enviro-card">
            <div class="enviro-header">
                <span>Recent Activities</span>
                <span class="indicator-pill green" style="font-size: 10px; padding: 2px 6px;">Live</span>
            </div>
            <div id="notification-list" style="max-height: 400px; overflow-y: auto;">
                <div class="text-muted p-3">Loading activities...</div>
            </div>
        </div>
        """,
		css="""
        .enviro-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 18px; margin-bottom: 24px; box-shadow: var(--shadow-sm); }
        .enviro-header { display: flex; justify-content: space-between; align-items: center; font-weight: 700; font-size: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        .activity-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--border-color); }
        .activity-item:last-child { border-bottom: none; }
        .activity-text { font-size: 13px; font-weight: 500; color: var(--text-color); }
        .activity-time { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
        """,
		script="""
        frappe.call({
            method: "enviro.enviro.api.dashboard.get_home_dashboard_data",
            callback: function(r) {
                if (r.message && r.message.notifications) {
                    let html = "";
                    r.message.notifications.forEach(n => {
                        html += `
                            <div class="activity-item">
                                <div style="flex: 1; margin-right: 10px;">
                                    <div class="activity-text">${n.title}</div>
                                    <div class="activity-time">${frappe.datetime.global_date_format(n.timestamp)}</div>
                                </div>
                                <button class="btn btn-xs btn-outline-primary" style="flex-shrink: 0;" onclick="frappe.set_route('Form', '${n.doctype}', '${n.docname}')">View</button>
                            </div>
                        `;
                    });
                    document.getElementById("notification-list").innerHTML = html || '<div class="text-muted p-4 text-center">No recent activities</div>';
                }
            }
        });
        """,
	)

	# 2. Daily Schedule Grid
	create_block(
		name="Enviro Home Schedule Grid",
		html="""
        <div class="enviro-card">
            <div class="enviro-header">Today's Schedule</div>
            <div id="schedule-grid" class="grid-2x2">
                <div class="text-muted p-3">Fetching...</div>
            </div>
        </div>
        """,
		css="""
        .grid-2x2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 10px; }
        .grid-item { background: var(--bg-color); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .grid-item:hover { transform: translateY(-3px); border-color: var(--p-primary); box-shadow: var(--shadow-sm); }
        .grid-time { font-size: 15px; font-weight: 700; color: var(--p-primary); margin-bottom: 4px; }
        .grid-cust { font-size: 11px; font-weight: 500; opacity: 0.8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        """,
		script="""
        frappe.call({
            method: "enviro.enviro.api.dashboard.get_home_dashboard_data",
            callback: function(r) {
                if (r.message && r.message.todays_schedule) {
                    let grid = "";
                    r.message.todays_schedule.forEach(s => {
                        grid += `
                            <div class="grid-item" onclick="frappe.set_route('Form', 'Enviro Job', '${s.name}')">
                                <div class="grid-time">${s.scheduled_start_time}</div>
                                <div class="grid-cust">${s.customer_name}</div>
                            </div>
                        `;
                    });
                    document.getElementById("schedule-grid").innerHTML = grid || '<div class="text-muted p-4 text-center col-span-2">No jobs scheduled today</div>';
                }
            }
        });
        """,
	)

	# 3. Weather Widget
	create_block(
		name="Enviro Home Weather",
		html="""
        <div id="enviro-weather" class="enviro-card weather-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                   <div id="w-temp" style="font-size: 36px; font-weight: 800;">--°C</div>
                   <div id="w-desc" style="font-size: 14px; opacity: 0.8; text-transform: capitalize;">Loading...</div>
                </div>
                <div style="text-align: right">
                   <div style="font-weight: 600; font-size: 14px;">Riyadh</div>
                   <div id="w-date" style="font-size: 11px; opacity: 0.6;">Today</div>
                </div>
            </div>
            <div id="w-forecast" style="display: flex; justify-content: space-between; margin-top: 24px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 16px;">
            </div>
        </div>
        """,
		css="""
        .weather-card { background: linear-gradient(135deg, #374151 0%, #111827 100%) !important; color: #fff !important; border: none !important; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); }
        .forecast-day { text-align: center; flex: 1; }
        .f-temp { font-size: 13px; font-weight: 600; }
        .f-time { font-size: 9px; opacity: 0.5; margin-top: 2px; }
        """,
		script="""
        const KEY = "6d3c8c4f5f6b8f9e0d1c2b3a4f5e6d7c"; // Placeholder - User should replace
        const CITY = "Riyadh";
        document.getElementById("w-date").innerText = new Date().toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short"});

        async function loadWeather() {
            try {
                let res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${CITY}&units=metric&appid=${KEY}`);
                let data = await res.json();
                if(data.main) {
                    document.getElementById("w-temp").innerText = Math.round(data.main.temp) + "°C";
                    document.getElementById("w-desc").innerText = data.weather[0].description;
                }

                let f_res = await fetch(`https://api.openweathermap.org/data/2.5/forecast?q=${CITY}&units=metric&cnt=5&appid=${KEY}`);
                let f_data = await f_res.json();
                if(f_data.list) {
                    let html = "";
                    f_data.list.forEach(f => {
                         html += `
                            <div class="forecast-day">
                                <div class="f-temp">${Math.round(f.main.temp)}°</div>
                                <div class="f-time">${f.dt_txt.slice(11,13)}h</div>
                            </div>`;
                    });
                    document.getElementById("w-forecast").innerHTML = html;
                }
            } catch(e) { document.getElementById("w-desc").innerText = "API Key Error"; }
        }
        loadWeather();
        """,
	)

	# 4. Job List
	create_block(
		name="Enviro Home Job List",
		html="""
        <div class="enviro-card">
            <div class="enviro-header">Job Inventory</div>
            <div class="table-responsive">
                <table class="table table-sm" style="font-size: 12px; margin-bottom: 0;">
                    <thead>
                        <tr class="text-muted">
                            <th>CODE</th>
                            <th>CUSTOMER</th>
                            <th>STATUS</th>
                        </tr>
                    </thead>
                    <tbody id="job-table-body">
                    </tbody>
                </table>
            </div>
            <div class="text-center mt-3">
                <button class="btn btn-xs btn-default w-full" onclick="frappe.set_route('List', 'Enviro Job')">View All Jobs</button>
            </div>
        </div>
        """,
		css="""
        #job-table-body tr { transition: background 0.1s; }
        #job-table-body tr:hover { background: var(--bg-color); }
        """,
		script="""
        frappe.call({
            method: "enviro.enviro.api.dashboard.get_home_dashboard_data",
            callback: function(r) {
                if (r.message && r.message.all_jobs) {
                    let rows = "";
                    r.message.all_jobs.forEach(j => {
                        rows += `
                            <tr style="cursor: pointer" onclick="frappe.set_route('Form', 'Enviro Job', '${j.code}')">
                                <td style="font-weight: 600;">${j.code}</td>
                                <td>${j.title}</td>
                                <td><span class="indicator-pill ${j.status == 'Done' ? 'green' : 'orange'}" style="font-size: 10px;">${j.status}</span></td>
                            </tr>
                        `;
                    });
                    document.getElementById("job-table-body").innerHTML = rows || '<tr><td colspan="3" class="text-center p-3 text-muted">No jobs found</td></tr>';
                }
            }
        });
        """,
	)
	frappe.db.commit()


def create_block(name, html, css, script):
	if frappe.db.exists("Custom HTML Block", name):
		doc = frappe.get_doc("Custom HTML Block", name)
		doc.html = html
		doc.style = css
		doc.script = script
		# Ensure 'All' role exists for public visibility
		if not any(r.role == "All" for r in doc.roles):
			doc.append("roles", {"role": "All"})
		doc.save()
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Custom HTML Block",
				"name": name,
				"html": html,
				"style": css,
				"script": script,
				"roles": [{"role": "All"}],
			}
		)
		doc.insert()
