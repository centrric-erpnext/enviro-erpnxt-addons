/**
 * Enviro HR Workspace Dashboard
 * Loaded globally via app_include_js — initializes the HR block
 * whenever it appears in the DOM (workspace custom block rendering).
 */

(function () {
	"use strict";

	/* ── State ── */
	var HR = {
		cur: "leave",
		aL: [],
		aT: [],
		ready: false,
	};

	/* ── Helpers ── */
	function ini(n) {
		return (n || "?")
			.split(" ")
			.map(function (w) {
				return w[0] || "";
			})
			.slice(0, 2)
			.join("")
			.toUpperCase();
	}
	function av(r) {
		var t = ini(r.employee_name);
		if (r.photo)
			return (
				'<div class="hav"><img src="' +
				r.photo +
				'" onerror="this.outerHTML=\'<span>' +
				t +
				"</span>'\"></div>"
			);
		return '<div class="hav">' + t + "</div>";
	}
	function bdg(s) {
		var m = {
			Approved: "b-app",
			Rejected: "b-rej",
			Pending: "b-pen",
			Open: "b-ope",
			Draft: "b-dra",
			Cancelled: "b-can",
		};
		return '<span class="hbdg ' + (m[s] || "b-dra") + '">' + s + "</span>";
	}
	function $id(id) {
		return document.getElementById(id);
	}
	function setBody(h) {
		var b = $id("hr-body");
		if (b) {
			b.innerHTML = h;
		}
	}
	function spin() {
		return (
			'<div style="text-align:center;padding:48px;color:#6b7280;">' +
			'<div style="border:3px solid #e5e7eb;border-top-color:#2563eb;border-radius:50%;' +
			'width:28px;height:28px;animation:hrspin .7s linear infinite;margin:0 auto 10px;"></div>Loading…</div>'
		);
	}

	/* ── API ── */
	function api(method, args) {
		return new Promise(function (ok, fail) {
			frappe.call({
				method: "enviro.api.hr." + method,
				args: args || {},
				callback: function (r) {
					ok(r.message || []);
				},
				error: function (e) {
					fail(e);
				},
			});
		});
	}

	/* ── Tab ── */
	function setTab(t) {
		HR.cur = t;
		var lb = $id("hr-tab-leave"),
			tb = $id("hr-tab-ts");
		var cl = $id("hr-cnt-leave"),
			ct = $id("hr-cnt-ts");
		if (!lb || !tb) return;

		if (t === "leave") {
			lb.className = "btn btn-sm btn-primary";
			lb.style.cssText = "border-radius:50px;padding:6px 18px;font-weight:600;";
			tb.className = "btn btn-sm btn-default";
			tb.style.cssText =
				"border-radius:50px;padding:6px 18px;font-weight:600;border:1.5px solid #d1d5db;";
			if (cl)
				cl.style.cssText =
					"background:rgba(255,255,255,.3);color:#fff;border-radius:20px;padding:1px 8px;font-size:11px;";
			if (ct)
				ct.style.cssText =
					"background:#e9ecef;color:#495057;border-radius:20px;padding:1px 8px;font-size:11px;";
			renderLeave(HR.aL);
		} else {
			tb.className = "btn btn-sm btn-primary";
			tb.style.cssText = "border-radius:50px;padding:6px 18px;font-weight:600;";
			lb.className = "btn btn-sm btn-default";
			lb.style.cssText =
				"border-radius:50px;padding:6px 18px;font-weight:600;border:1.5px solid #d1d5db;";
			if (ct)
				ct.style.cssText =
					"background:rgba(255,255,255,.3);color:#fff;border-radius:20px;padding:1px 8px;font-size:11px;";
			if (cl)
				cl.style.cssText =
					"background:#e9ecef;color:#495057;border-radius:20px;padding:1px 8px;font-size:11px;";
			renderTS(HR.aT);
		}

		var q = $id("hr-search");
		if (q) q.value = "";
	}

	/* ── Search ── */
	function filterNow() {
		var q = ($id("hr-search") || {}).value || "";
		q = q.toLowerCase();
		if (HR.cur === "leave")
			renderLeave(
				HR.aL.filter(function (r) {
					return (r.employee_name || "").toLowerCase().indexOf(q) !== -1;
				})
			);
		else
			renderTS(
				HR.aT.filter(function (r) {
					return (r.employee_name || "").toLowerCase().indexOf(q) !== -1;
				})
			);
	}

	/* ── Render Leave ── */
	function renderLeave(rows) {
		var cl = $id("hr-cnt-leave");
		if (cl) cl.textContent = rows.length;
		if (!rows.length) {
			setBody(
				'<div style="text-align:center;padding:48px;color:#9ca3af;">No leave applications found.</div>'
			);
			return;
		}
		var h =
			'<div style="overflow-x:auto;"><table id="hr-tbl-leave"><thead><tr>' +
			"<th>Employee</th><th>Leave From</th><th>Leave To</th>" +
			"<th>Assigned Jobs</th><th>Leave Type</th><th>Attachments</th><th>Action</th>" +
			"</tr></thead><tbody>";
		rows.forEach(function (r) {
			var att = '<span style="color:#9ca3af;font-size:12px;">No Attachment</span>';
			if (r.attachments && r.attachments.length)
				att = r.attachments
					.map(function (u, i) {
						return (
							'<a href="' +
							u +
							'" target="_blank" style="color:#2563eb;font-size:12px;">📎 File ' +
							(i + 1) +
							"</a>"
						);
					})
					.join("<br>");
			h +=
				"<tr>" +
				"<td><div style='display:flex;align-items:center;gap:8px;'>" +
				av(r) +
				"<strong style='color:#111827;'>" +
				r.employee_name +
				"</strong></div></td>" +
				"<td>" +
				r.from_date +
				"</td><td>" +
				r.to_date +
				"</td>" +
				"<td style='color:#6b7280;font-size:12px;'>" +
				r.assigned_jobs +
				"</td>" +
				"<td>📄 " +
				r.leave_type +
				"</td>" +
				"<td>" +
				att +
				"</td>" +
				"<td style='min-width:110px;'>" +
				'<button class="lpill lpill-g" data-action="approve" data-name="' +
				r.name +
				'">' +
				(r.status === "Approved" ? "✓ Approved" : "Approve") +
				"</button>" +
				'<button class="lpill lpill-r" data-action="delete"  data-name="' +
				r.name +
				'" style="margin-top:3px;">Delete</button>' +
				(r.status !== "Rejected" && r.status !== "Approved"
					? '<button class="lpill lpill-r" data-action="reject" data-name="' +
					  r.name +
					  '" style="margin-top:3px;background:#dc2626;">Reject</button>'
					: "") +
				"</td></tr>";
		});
		setBody(h + "</tbody></table></div>");
	}

	/* ── Render Timesheets ── */
	function renderTS(rows) {
		var ct = $id("hr-cnt-ts");
		if (ct) ct.textContent = rows.length;
		if (!rows.length) {
			setBody(
				'<div style="text-align:center;padding:48px;color:#9ca3af;">No weekly timesheets found.</div>'
			);
			return;
		}
		var h =
			'<div style="overflow-x:auto;"><table id="hr-tbl-ts"><thead><tr>' +
			"<th>Employee</th><th>TimeSheet Last Updated</th><th>TimeSheet Week</th>" +
			"<th>TimeSheet View</th><th>TimeSheet Access Log View</th><th>TimeSheet Status</th>" +
			"</tr></thead><tbody>";
		rows.forEach(function (r) {
			var week = r.week_beginning + (r.week_end ? " - " + r.week_end : "");
			var statusBtn = "";
			if (r.status === "Approved")
				statusBtn =
					'<span class="hbdg b-app" style="display:block;text-align:center;padding:6px 0;">✓ Approved</span>';
			else if (r.status === "Rejected")
				statusBtn =
					'<span class="hbdg b-rej" style="display:block;text-align:center;padding:6px 0;">Rejected</span>' +
					'<button class="tbtn-app" data-ts-action="approve" data-name="' +
					r.name +
					'" style="margin-top:4px;">Approve</button>';
			else
				statusBtn =
					'<button class="tbtn-app" data-ts-action="approve" data-name="' +
					r.name +
					'">Approve</button>';

			h +=
				"<tr>" +
				"<td><strong style='color:#111827;'>" +
				r.employee_name +
				"</strong></td>" +
				"<td style='color:#6b7280;'>" +
				r.last_updated +
				"</td>" +
				"<td style='white-space:nowrap;'>" +
				week +
				"</td>" +
				"<td>" +
				'<button class="tbtn tbtn-v" data-ts-view="' +
				r.name +
				'">View</button>' +
				'<button class="tbtn tbtn-d" data-ts-action="delete" data-name="' +
				r.name +
				'">Delete</button>' +
				"</td>" +
				"<td><button class='tbtn tbtn-v' data-ts-log='" +
				r.employee +
				"'>View</button></td>" +
				"<td style='min-width:120px;'>" +
				statusBtn +
				"</td>" +
				"</tr>";
		});
		setBody(h + "</tbody></table></div>");
	}

	/* ── Actions (called via event delegation) ── */
	function handleLeaveAction(action, name) {
		var lbl = { approve: "Approve", reject: "Reject", delete: "Delete" }[action];
		frappe.confirm(lbl + " this leave application?", function () {
			api(
				{ approve: "approve_leave", reject: "reject_leave", delete: "delete_leave" }[
					action
				],
				{ name: name }
			)
				.then(function () {
					frappe.show_alert({ message: "Leave " + lbl + "d", indicator: "green" });
					loadAll();
				})
				.catch(function () {
					frappe.msgprint("Action failed.");
				});
		});
	}
	function handleTSAction(action, name) {
		var lbl = { approve: "Approve", reject: "Reject", delete: "Delete" }[action];
		frappe.confirm(lbl + " this timesheet?", function () {
			api(
				{
					approve: "approve_timesheet",
					reject: "reject_timesheet",
					delete: "delete_timesheet",
				}[action],
				{ name: name }
			)
				.then(function () {
					frappe.show_alert({ message: "Timesheet " + lbl + "d", indicator: "green" });
					loadAll();
				})
				.catch(function () {
					frappe.msgprint("Action failed.");
				});
		});
	}

	/* ── Load data ── */
	function loadAll() {
		setBody(spin());
		Promise.all([api("get_leave_applications"), api("get_timesheets")])
			.then(function (res) {
				HR.aL = res[0] || [];
				HR.aT = res[1] || [];
				var cl = $id("hr-cnt-leave"),
					ct = $id("hr-cnt-ts");
				if (cl) cl.textContent = HR.aL.length;
				if (ct) ct.textContent = HR.aT.length;
				if (HR.cur === "leave") renderLeave(HR.aL);
				else renderTS(HR.aT);
			})
			.catch(function (e) {
				console.error("HR Dashboard error:", e);
				setBody(
					'<div style="text-align:center;padding:48px;color:#dc2626;">⚠ Failed to load. Please refresh.</div>'
				);
			});
	}

	/* ── Attach events to the block ── */
	function initBlock() {
		var root = $id("hr-root");
		if (!root || HR.ready) return;
		HR.ready = true;

		/* Tab clicks */
		var tl = $id("hr-tab-leave"),
			tt = $id("hr-tab-ts");
		if (tl)
			tl.addEventListener("click", function (e) {
				e.stopPropagation();
				setTab("leave");
			});
		if (tt)
			tt.addEventListener("click", function (e) {
				e.stopPropagation();
				setTab("timesheet");
			});

		/* Search input — stop Frappe's global keyboard shortcuts */
		var srch = $id("hr-search");
		if (srch) {
			["keydown", "keyup", "keypress", "input"].forEach(function (ev) {
				srch.addEventListener(ev, function (e) {
					e.stopPropagation();
					if (ev === "input" || ev === "keyup") filterNow();
				});
			});
			srch.addEventListener("click", function (e) {
				e.stopPropagation();
				srch.focus();
			});
		}

		/* Event delegation on body for action buttons */
		var body = $id("hr-body");
		if (body) {
			body.addEventListener("click", function (e) {
				var el = e.target;
				var la = el.getAttribute("data-action");
				var ln = el.getAttribute("data-name");
				if (la && ln) {
					e.stopPropagation();
					handleLeaveAction(la, ln);
					return;
				}

				var tv = el.getAttribute("data-ts-view");
				if (tv) {
					e.stopPropagation();
					frappe.set_route("Form", "Enviro Weekly Timesheet", tv);
					return;
				}

				var tlog = el.getAttribute("data-ts-log");
				if (tlog) {
					e.stopPropagation();
					frappe.set_route("List", "Enviro Weekly Timesheet", { employee: tlog });
					return;
				}

				var ta = el.getAttribute("data-ts-action");
				var tn = el.getAttribute("data-name");
				if (ta && tn) {
					e.stopPropagation();
					handleTSAction(ta, tn);
				}
			});
		}

		/* Load initial data */
		loadAll();
	}

	/* ── MutationObserver — watches for the block to appear in the DOM ── */
	function watchForBlock() {
		if ($id("hr-root")) {
			initBlock();
			return;
		}

		var obs = new MutationObserver(function () {
			if ($id("hr-root")) {
				obs.disconnect();
				/* small delay lets Frappe finish rendering */
				setTimeout(function () {
					HR.ready = false;
					initBlock();
				}, 200);
			}
		});
		obs.observe(document.body, { childList: true, subtree: true });
	}

	/* ── Boot ── */
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", watchForBlock);
	} else {
		watchForBlock();
	}

	/* Re-init when frappe route changes (SPA navigation) */
	if (typeof frappe !== "undefined" && frappe.router) {
		frappe.router.on("change", function () {
			HR.ready = false;
			setTimeout(watchForBlock, 300);
		});
	}
})();
