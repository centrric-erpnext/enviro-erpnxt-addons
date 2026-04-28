import frappe


@frappe.whitelist()
def run_setup():
	html = """
    <div class="dashboard-container">
        <!-- Header Section -->
        <div class="dashboard-header">
            <div class="logo-area">
                <span class="enviro-logo-text">enviro</span>
                <span class="logo-subtext">waste services group</span>
            </div>
            <div class="header-info">
                <span id="header-date">--</span>
            </div>
        </div>

        <!-- Grid Layout -->
        <div class="dashboard-grid">
            <!-- Row 1: Notifications | Sales | Safety -->
            <div class="card-column">
                <div class="dashboard-card">
                    <div class="card-header">
                        <span>Notifications</span>
                        <div class="header-actions">
                            <span class="action-btn">Add New</span>
                            <span class="action-btn blue">See All</span>
                        </div>
                    </div>
                    <div id="unified-notifications" class="card-body scrollable">
                        <div class="text-muted p-4 text-center">Loading...</div>
                    </div>
                </div>
            </div>

            <div class="card-column">
                <div class="dashboard-card">
                    <div class="card-header">
                        <span>Sales</span>
                        <span class="action-btn blue">See All</span>
                    </div>
                    <div class="card-body">
                        <div id="sales-chart" style="height: 180px;"></div>
                    </div>
                </div>
            </div>

            <div class="card-column">
                <div class="dashboard-card">
                    <div class="card-header">
                        <span>Safety Data</span>
                        <span class="action-btn blue">See All</span>
                    </div>
                    <div class="card-body" id="safety-data-container">
                        <div class="safety-row">
                           <div class="safety-sub-header">People</div>
                           <div class="safety-stats">
                               <div class="stat-pill">MTD: <span id="s-p-mtd">--</span></div>
                               <div class="stat-pill">YTD: <span id="s-p-ytd">--</span></div>
                           </div>
                        </div>
                        <div class="safety-labels">
                            <span>LTI: no Data</span>
                            <span>MTD: no Data</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Row 2: Job List | Schedule | Weather -->
            <div class="card-column">
                <div class="dashboard-card">
                    <div class="card-header">
                        <span>List of all Jobs</span>
                        <span class="action-btn blue">See All</span>
                    </div>
                    <div id="unified-jobs" class="card-body scrollable" style="padding: 0;">
                        <table class="enviro-table">
                            <thead><tr><th>Code</th><th>Title</th><th>Status</th></tr></thead>
                            <tbody id="job-rows"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="card-column">
                <div class="dashboard-card">
                    <div class="card-header">
                        <span>Schedule for the day</span>
                        <span class="action-btn blue">See All</span>
                    </div>
                    <div id="unified-schedule" class="card-body grid-2x2">
                        <div class="empty-slot">+</div>
                        <div class="empty-slot">+</div>
                    </div>
                </div>
            </div>

            <div class="card-column">
                <div class="dashboard-card weather-bg">
                    <div class="card-header" style="border:none; color: white;">
                        <span>Weather</span>
                    </div>
                    <div class="card-body text-white" style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div id="u-temp" style="font-size: 38px; font-weight: 700;">--°C</div>
                            <div id="u-desc" style="font-size: 14px; opacity: 0.8;">Loading...</div>
                        </div>
                        <div id="u-forecast" class="mini-forecast"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

	css = """
    .dashboard-container { padding: 20px; background: #f8fafc; font-family: 'Inter', sans-serif; }
    .dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
    .enviro-logo-text { font-size: 32px; font-weight: 800; color: #0ea5e9; letter-spacing: -1px; }
    .logo-subtext { display: block; font-size: 10px; text-transform: uppercase; color: #64748b; margin-top: -5px; }

    .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
    .dashboard-card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden; height: 100%; display: flex; flex-direction: column; min-height: 250px; }
    .card-header { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; font-weight: 600; color: #334155; font-size: 14px; background: #fcfdfe; }
    .card-body { padding: 16px; flex: 1; position: relative; }
    .scrollable { max-height: 200px; overflow-y: auto; }

    .action-btn { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 4px; cursor: pointer; color: #64748b; background: #f1f5f9; margin-left: 5px; }
    .action-btn.blue { color: #0ea5e9; background: #f0f9ff; }

    .enviro-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .enviro-table th { text-align: left; padding: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #f1f5f9; }
    .enviro-table td { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #475569; }

    .grid-2x2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .empty-slot { background: #f1f5f9; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #94a3b8; border: 2px dashed #e2e8f0; min-height: 80px; }

    .weather-bg { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: none; }
    .stat-pill { background: #f0f9ff; color: #0891b2; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-right: 5px; }
    .text-white { color: white !important; }

    .activity-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }
    .act-title { font-size: 12px; font-weight: 500; }
    .act-view { font-size: 10px; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
    """

	script = """
    function updateDashboard() {
        document.getElementById('header-date').innerText = new Date().toLocaleDateString(undefined, {weekday:'long', year:'numeric', month:'long', day:'numeric'});

        frappe.call({
            method: "enviro.enviro.api.dashboard.get_home_dashboard_data",
            callback: function(r) {
                if(r.message) {
                    // 1. Notifications
                    let n_html = r.message.notifications.map(n => `
                        <div class="activity-row">
                            <div class="act-title">${n.title}</div>
                            <div class="act-view" onclick="frappe.set_route('Form', '${n.doctype}', '${n.docname}')">View</div>
                        </div>
                    `).join('') || '<div class="text-muted text-center p-4">No new notifications</div>';
                    document.getElementById('unified-notifications').innerHTML = n_html;

                    // 2. Sales Chart
                    if(r.message.sales_data) {
                        try {
                            new frappe.Chart("#sales-chart", {
                                data: r.message.sales_data,
                                type: 'axis-mixed',
                                height: 180,
                                colors: ['#0ea5e9'],
                                lineOptions: { regionFill: 1 }
                            });
                        } catch(e) {}
                    }

                    // 3. Safety Data
                    if(r.message.safety_data) {
                        document.getElementById('s-p-mtd').innerText = r.message.safety_data.people.mtd;
                        document.getElementById('s-p-ytd').innerText = r.message.safety_data.people.ytd;
                    }

                    // 4. Job List
                    let j_html = r.message.all_jobs.map(j => `
                        <tr>
                            <td class="font-bold">${j.code}</td>
                            <td>${j.title}</td>
                            <td><span class="indicator-pill ${j.status == 'Done' ? 'green' : 'orange'}">${j.status}</span></td>
                        </tr>
                    `).join('') || '<tr><td colspan="3" class="text-center p-3">No jobs found</td></tr>';
                    document.getElementById('job-rows').innerHTML = j_html;

                    // 5. Schedule (Simplified Grid)
                    if(r.message.todays_schedule && r.message.todays_schedule.length > 0) {
                        let s_html = "";
                        r.message.todays_schedule.forEach(s => {
                            s_html += `<div class="empty-slot" style="background:#f0fdf4; border-color:#bbf7d0; color:#16a34a; font-size:12px; font-weight:700;">${s.customer_name}</div>`;
                        });
                        while(s_html.match(/empty-slot/g || []).length < 2) s_html += '<div class="empty-slot">+</div>';
                        document.getElementById('unified-schedule').innerHTML = s_html;
                    }

                    // 6. Weather
                    if(r.message.weather_placeholder == false) { /* logic if we had key */ }
                }
            }
        });
    }

    // Init weather independently for speed
    async function loadUnifiedWeather() {
        const KEY = "6d3c8c4f5f6b8f9e0d1c2b3a4f5e6d7c";
        try {
            let res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=Riyadh&units=metric&appid=${KEY}`);
            let data = await res.json();
            if(data.main) {
                document.getElementById('u-temp').innerText = Math.round(data.main.temp) + "°C";
                document.getElementById('u-desc').innerText = data.weather[0].description;
            }
        } catch(e) {}
    }

    updateDashboard();
    loadUnifiedWeather();
    """

	# Register only ONE block that contains everything
	name = "Enviro Unified Dashboard Master"
	if frappe.db.exists("Custom HTML Block", name):
		doc = frappe.get_doc("Custom HTML Block", name)
		doc.html = html
		doc.style = css
		doc.script = script
		if not any(r.role == "System Manager" for r in doc.roles):
			doc.append("roles", {"role": "System Manager"})
		doc.save()
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Custom HTML Block",
				"name": name,
				"html": html,
				"style": css,
				"script": script,
				"roles": [{"role": "System Manager"}],
			}
		)
		doc.insert()

	frappe.db.commit()  # nosemgrep
	print(f"Registered {name}")
