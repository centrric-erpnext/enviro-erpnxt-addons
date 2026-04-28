import frappe

script_content = """
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
                        while((s_html.match(/empty-slot/g) || []).length < 2) s_html += '<div class="empty-slot">+</div>';
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

frappe.db.set_value("Custom HTML Block", "Enviro Unified Dashboard Master", "script", script_content)
frappe.db.commit()  # nosemgrep
print("DASHBOARD_SCRIPT_UPDATED_FULL")
