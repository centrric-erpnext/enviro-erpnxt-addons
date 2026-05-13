/* global root_element, _ */
(function () {
	const manager_roles = [
		"HR Manager",
		"System Manager",
		"CEO",
		"Administrator",
		"Superadmin",
		"Director",
	];
	const is_manager = frappe.user_roles.some((role) => manager_roles.includes(role));

	const styles = `
        <style>
            .env-wrapper { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f9fafb; padding: 20px; border-radius: 8px; }
            .env-header-bar { display: flex; justify-content: space-between; background: #e5e7eb; padding: 10px; border-radius: 30px; margin-bottom: 20px; align-items: center; }
            .env-section-title { font-size: 18px; font-weight: bold; color: #374151; margin: 30px 0 15px 10px; display: flex; justify-content: space-between; align-items: center; }
            .env-search { padding: 8px 15px; border-radius: 20px; border: 1px solid #d1d5db; width: 250px; outline: none; }
            .env-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; }
            .env-card { background: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); cursor: pointer; transition: 0.2s; }
            .env-card:hover { transform: translateY(-3px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            .env-avatar { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; margin-bottom: 10px; background: #e5e7eb; display: inline-flex; align-items: center; justify-content: center; font-size: 20px; color: #9ca3af; }
            .env-name { color: #0ea5e9; font-weight: bold; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

            .env-folder-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
            .env-folder { border: 1px solid #e5e7eb; background: #ffffff; border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 10px; cursor: pointer; color: #4b5563; font-size: 13px; font-weight: 500; transition: 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            .env-folder:hover { background: #f3f4f6; border-color: #d1d5db; transform: translateY(-2px); }
            .env-file { border: 1px dashed #cbd5e1; background: #f8fafc; border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 10px; cursor: pointer; color: #3b82f6; font-size: 13px; font-weight: 500; transition: 0.2s; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
            .env-file:hover { background: #e0f2fe; border-color: #7dd3fc; }

            .env-action-btn { background: white; border: 1px solid #d1d5db; border-radius: 20px; padding: 6px 15px; font-size: 12px; font-weight: bold; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; transition: 0.2s; }
            .env-action-btn.primary { background: #0ea5e9; color: white; border-color: #0ea5e9; }
            .env-action-btn.primary:hover { background: #0284c7; }
            .env-badge { padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; background: #e0f2fe; color: #0369a1; }

            .env-scroll-container { max-height: 400px; overflow-y: auto; padding-right: 5px; margin-bottom: 20px; }
            .env-scroll-container::-webkit-scrollbar { width: 6px; }
            .env-scroll-container::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
        </style>
    `;

	function renderManagerDashboard() {
		root_element.innerHTML =
			styles +
			`
            <div class="env-wrapper">
                <div class="env-header-bar">
                    <div style="font-weight: bold; color: #374151; font-size: 16px; margin-left: 10px;">Team Dashboard</div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="text" id="env-local-search" class="env-search" placeholder="Search employee 🔍">
                        <button class="env-action-btn primary" id="env-add-emp-btn">+ Add Employee</button>
                    </div>
                </div>

                <div class="env-section-title">Current Employees</div>
                <div id="env-employee-container" class="env-scroll-container">
                    <div style="text-align: center; padding: 40px; color: #9ca3af;">Loading Employees...</div>
                </div>

                <div class="env-section-title">
                    <span>Common Folders & Documents</span>
                    <button class="env-action-btn primary" id="env-add-folder-btn">+ Add Folder</button>
                </div>
                <div id="env-folder-container" style="min-height: 300px;">
                    <div style="text-align: center; padding: 40px; color: #9ca3af;">Loading Folders...</div>
                </div>
            </div>
        `;

		drawEmployees();
		drawTeamFolders();

		root_element
			.querySelector("#env-add-emp-btn")
			.addEventListener("click", () => frappe.new_doc("Employee"));

		const searchInput = root_element.querySelector("#env-local-search");
		if (searchInput) {
			searchInput.addEventListener("keydown", (e) => e.stopPropagation());
			searchInput.addEventListener("input", (e) => {
				e.stopPropagation();
				const searchTerm = e.target.value.toLowerCase();
				root_element.querySelectorAll(".env-card").forEach((card) => {
					const empName = card.querySelector(".env-name").innerText.toLowerCase();
					card.style.display = empName.includes(searchTerm) ? "block" : "none";
				});
			});
		}

		root_element.querySelector("#env-add-folder-btn").addEventListener("click", () => {
			frappe.prompt(
				[{ label: "Folder Name", fieldname: "folder_name", fieldtype: "Data", reqd: 1 }],
				(values) => {
					frappe.call({
						method: "frappe.client.insert",
						args: {
							doc: {
								doctype: "Enviro Team Folder",
								folder_name: values.folder_name,
							},
						},
						callback: (r) => {
							if (!r.exc) drawTeamFolders();
						},
					});
				},
				"New Folder",
				"Create"
			);
		});
	}

	function drawEmployees() {
		const container = root_element.querySelector("#env-employee-container");

		frappe.db
			.get_list("Employee", {
				fields: ["name", "employee_name", "image"],
				filters: { status: "Active" },
				limit: 100,
				order_by: "employee_name asc",
			})
			.then((employees) => {
				let html = '<div class="env-grid">';
				(employees || []).forEach((emp) => {
					let img_html = emp.image
						? `<img src="${emp.image}" class="env-avatar">`
						: '<div class="env-avatar">👤</div>';
					html += `
                    <div class="env-card" data-emp="${emp.name}">
                        ${img_html}
                        <div class="env-name">${emp.employee_name}</div>
                    </div>
                `;
				});
				html += "</div>";
				container.innerHTML = html;

				container.querySelectorAll(".env-card").forEach((card) => {
					card.addEventListener("click", function () {
						frappe.set_route("Form", "Employee", this.getAttribute("data-emp"));
					});
				});
			});
	}

	function drawTeamFolders() {
		const container = root_element.querySelector("#env-folder-container");

		Promise.all([
			frappe.db.get_list("Enviro Team Folder", { fields: ["name"], limit: 1000 }),
			frappe.db.get_list("File", {
				filters: { attached_to_doctype: "Enviro Team Folder" },
				fields: ["attached_to_name"],
				limit: 10000,
			}),
		]).then(([folders, allFiles]) => {
			let html = '<div class="env-folder-grid">';
			(folders || []).forEach((f) => {
				let count = (allFiles || []).filter(
					(file) => file.attached_to_name === f.name
				).length;
				html += `
                    <div class="env-folder" data-folder="${f.name}">
                        <div style="font-size: 24px; color: #fbbf24;">📁</div>
                        <div>
                            <div style="font-weight: bold;">${f.name}</div>
                            <div style="font-size: 11px; color: #9ca3af;">${count} files</div>
                        </div>
                    </div>
                `;
			});
			html += "</div>";
			container.innerHTML = html;

			container.querySelectorAll(".env-folder").forEach((el) => {
				el.addEventListener("click", function () {
					drawTeamFiles(this.getAttribute("data-folder"));
				});
			});
		});
	}

	function drawTeamFiles(folderName) {
		const container = root_element.querySelector("#env-folder-container");
		container.innerHTML =
			'<div style="text-align: center; padding: 40px; color: #9ca3af;">Loading Files...</div>';

		frappe.db
			.get_list("File", {
				filters: {
					attached_to_doctype: "Enviro Team Folder",
					attached_to_name: folderName,
				},
				fields: ["name", "file_name", "file_url"],
				limit: 1000,
			})
			.then((files) => {
				let html = `
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                    <button class="env-action-btn" id="env-back-btn">⬅ Back to Folders</button>
                    <h3 style="margin: 0; color: #374151; font-size:16px;">📁 ${folderName}</h3>
                    <button class="env-action-btn primary" id="btn-upload-team-file" style="margin-left: auto;">+ Upload Document</button>
                </div>
                <div class="env-folder-grid">
            `;

				if (!files || files.length === 0) {
					html +=
						'<div style="grid-column: 1 / -1; padding: 20px; color: #9ca3af; font-style: italic; text-align:center;">No documents in this folder yet.</div>';
				} else {
					files.forEach((f) => {
						html += `<div class="env-file" title="${f.file_name}" data-url="${f.file_url}">📄 ${f.file_name}</div>`;
					});
				}

				html += "</div>";
				container.innerHTML = html;

				root_element
					.querySelector("#env-back-btn")
					.addEventListener("click", drawTeamFolders);

				root_element
					.querySelector("#btn-upload-team-file")
					.addEventListener("click", () => {
						new frappe.ui.FileUploader({
							doctype: "Enviro Team Folder",
							docname: folderName,
							on_success: (file_doc) => {
								frappe.show_alert({
									message: "File uploaded successfully!",
									indicator: "green",
								});
								drawTeamFiles(folderName);
							},
						});
					});

				container.querySelectorAll(".env-file").forEach((el) => {
					el.addEventListener("click", function () {
						window.open(this.getAttribute("data-url"), "_blank");
					});
				});
			});
	}

	function renderEmployeeProfile() {
		frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
			if (r && r.message) {
				let employee_id = r.message.name;
				Promise.all([
					frappe.db.get_doc("Employee", employee_id),
					frappe.db.get_list("File", {
						filters: {
							attached_to_doctype: "Employee",
							attached_to_name: employee_id,
						},
						fields: ["file_name", "file_url"],
						limit: 1000,
					}),
					frappe.db.get_value("User", frappe.session.user, "mobile_no"),
				]).then(([doc, files, user_res]) => {
					let user_mobile =
						user_res && user_res.message ? user_res.message.mobile_no : null;
					let envUserFiles = files || [];
					let img_html = doc.image
						? `<img src="${doc.image}" class="env-profile-pic">`
						: '<div class="env-profile-pic" style="display:flex; align-items:center; justify-content:center; font-size:40px; color:#9ca3af;">👤</div>';
					let formatDate = (dateString) =>
						dateString ? frappe.datetime.str_to_user(dateString) : "N/A";
					const envFolders = {
						"Employee Contracts": ["contract", "agreement", "offer"],
						"Medical & Health": ["doctor", "medical", "certificate", "health"],
						"Leave Applications": ["leave", "annual", "holiday"],
						"Compliance & Policies": [
							"police",
							"check",
							"conduct",
							"policy",
							"induction",
						],
						"Other Documents": [],
					};
					function getFilesInFolder(folderName) {
						if (folderName === "Other Documents") {
							return envUserFiles.filter((f) => {
								let name = f.file_name.toLowerCase();
								let matchesOther = Object.entries(envFolders).some(
									([key, keywords]) => {
										if (key === "Other Documents") return false;
										return keywords.some((kw) => name.includes(kw));
									}
								);
								return !matchesOther;
							});
						}
						let keywords = envFolders[folderName];
						return envUserFiles.filter((f) => {
							let name = f.file_name.toLowerCase();
							return keywords.some((kw) => name.includes(kw));
						});
					}
					function triggerUpload(currentView, folderName = null) {
						new frappe.ui.FileUploader({
							doctype: "Employee",
							docname: employee_id,
							on_success: (file_doc) => {
								let promise = Promise.resolve();
								if (
									folderName &&
									folderName !== "Other Documents" &&
									envFolders[folderName].length > 0
								) {
									let kw = envFolders[folderName][0];
									if (!file_doc.file_name.toLowerCase().includes(kw)) {
										let new_name = kw + "_" + file_doc.file_name;
										promise = frappe.call({
											method: "frappe.client.set_value",
											args: {
												doctype: "File",
												name: file_doc.name,
												fieldname: "file_name",
												value: new_name,
											},
										});
									}
								}
								promise.then(() => {
									frappe.db
										.get_list("File", {
											filters: {
												attached_to_doctype: "Employee",
												attached_to_name: employee_id,
											},
											fields: ["file_name", "file_url"],
											limit: 1000,
										})
										.then((updated_files) => {
											envUserFiles = updated_files || [];
											if (currentView === "files") {
												drawFiles(folderName);
											} else {
												drawFolders();
											}
											frappe.show_alert({
												message: "File uploaded successfully!",
												indicator: "green",
											});
										});
								});
							},
						});
					}

					let profileHtml =
						styles +
						`
                        <div class="env-wrapper" style="padding: 0; background: transparent;">
                            <div class="env-banner">
                                <div style="display: flex; gap: 10px; align-items: flex-start;">
                                    <button class="env-action-btn" id="btn-timesheet">📅 Timesheet</button>
                                    <button class="env-action-btn" id="btn-leave">🏖️ Leave Application</button>
                                </div>
                            </div>
                            <div class="env-profile-container">
                                <div class="env-left-col">
                                    ${img_html}
                                    <h2 style="color: #0ea5e9; margin: 15px 0 20px 0;">${
										doc.employee_name
									}</h2>
                                    <div class="env-detail-row"><div class="env-detail-label">Joined Date</div><div>${formatDate(
										doc.date_of_joining
									)}</div></div>
                                    <div class="env-detail-row"><div class="env-detail-label">Position Title</div><div>${
										doc.custom_position_title ||
										doc.designation ||
										doc.employment_type ||
										"N/A"
									}</div></div>
                                    <div class="env-detail-row"><div class="env-detail-label">Contact No</div><div>${
										doc.cell_number ||
										user_mobile ||
										doc.personal_email ||
										"N/A"
									}</div></div>
                                    <div class="env-detail-row"><div class="env-detail-label">Email</div><div style="word-break: break-all;">${
										doc.company_email || "N/A"
									}</div></div>
                                    <div class="env-detail-row"><div class="env-detail-label">Employment Status</div><div>${
										doc.status
									}</div></div>
                                    <div class="env-detail-row"><div class="env-detail-label">DOB</div><div>${formatDate(
										doc.date_of_birth
									)}</div></div>
                                    <button class="env-action-btn primary" id="btn-update-info" style="margin-top: 20px; width: 100%; justify-content: center; padding: 10px;">Update Info</button>
                                </div>
                                <div class="env-right-col">
                                    <div id="env-folder-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;"></div>
                                    <div id="env-folder-grid" class="env-folder-grid"></div>
                                </div>
                            </div>
                        </div>
                    `;
					root_element.innerHTML = profileHtml;
					root_element
						.querySelector("#btn-timesheet")
						.addEventListener("click", () =>
							frappe.new_doc("Enviro Weekly Timesheet", { employee: doc.name })
						);
					root_element
						.querySelector("#btn-leave")
						.addEventListener("click", () =>
							frappe.set_route("List", "Leave Application")
						);
					root_element
						.querySelector("#btn-update-info")
						.addEventListener("click", () =>
							frappe.set_route("Form", "Employee", doc.name)
						);

					function drawFolders() {
						let header = root_element.querySelector("#env-folder-header");
						let grid = root_element.querySelector("#env-folder-grid");
						header.innerHTML =
							'<h3 style="margin: 0; color: #374151;">Folders</h3><button class="env-action-btn primary" id="btn-upload-folder">+ Upload Document</button>';
						let gridHtml = "";
						Object.keys(envFolders).forEach((folderName) => {
							let count = getFilesInFolder(folderName).length;
							let emoji = folderName === "Other Documents" ? "📂" : "📁";
							gridHtml += `<div class="env-folder" data-folder="${folderName}"><div style="font-size: 24px; color: #fbbf24;">${emoji}</div><div><div style="font-weight: bold;">${folderName}</div><div style="font-size: 11px; color: #9ca3af;">${count} files</div></div></div>`;
						});
						grid.innerHTML = gridHtml;
						header
							.querySelector("#btn-upload-folder")
							.addEventListener("click", () => triggerUpload("folders"));
						grid.querySelectorAll(".env-folder").forEach((el) => {
							el.addEventListener("click", function () {
								drawFiles(this.getAttribute("data-folder"));
							});
						});
					}

					function drawFiles(folderName) {
						let header = root_element.querySelector("#env-folder-header");
						let grid = root_element.querySelector("#env-folder-grid");
						header.innerHTML = `<div style="display: flex; align-items: center; gap: 10px;"><button class="env-action-btn" id="env-back-btn">⬅ Back</button><h3 style="margin: 0; color: #374151;">📁 ${folderName}</h3></div><button class="env-action-btn primary" id="btn-upload-file">+ Upload Document</button>`;
						let files_to_show = getFilesInFolder(folderName);
						let gridHtml = "";
						if (files_to_show.length === 0) {
							gridHtml =
								'<div style="grid-column: 1 / -1; padding: 20px; color: #9ca3af; font-style: italic;">No documents in this folder yet.</div>';
						} else {
							files_to_show.forEach((f) => {
								gridHtml += `<div class="env-file" title="${f.file_name}" data-url="${f.file_url}">📄 ${f.file_name}</div>`;
							});
						}
						grid.innerHTML = gridHtml;
						header
							.querySelector("#env-back-btn")
							.addEventListener("click", drawFolders);
						header
							.querySelector("#btn-upload-file")
							.addEventListener("click", () => triggerUpload("files", folderName));
						grid.querySelectorAll(".env-file").forEach((el) => {
							el.addEventListener("click", function () {
								window.open(this.getAttribute("data-url"), "_blank");
							});
						});
					}
					drawFolders();
				});
			} else {
				root_element.innerHTML =
					styles +
					'<div class="env-wrapper" style="color: #dc2626; text-align: center; padding: 40px;"><b>Error:</b> No Employee profile is linked to your current user account.</div>';
			}
		});
	}

	if (is_manager) {
		renderManagerDashboard();
	} else {
		renderEmployeeProfile();
	}
})();
