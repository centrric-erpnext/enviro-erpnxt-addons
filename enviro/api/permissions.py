import frappe

# ─────────────────────────────────────────────────────────────
# PERMISSION MATRIX (from approved spreadsheet screenshots)
# Format per module: [view, add, edit, delete, pre_inspection]
# Profile Edit and Personal Profile Only handled separately.
# Waste / Pumps / Hills / Destruction columns are SKIPPED.
# ─────────────────────────────────────────────────────────────

T, F = True, False

FULL = [T, T, T, T, T]  # full CRUD + pre-inspection
VIEW_EDIT = [T, F, T, F, T]  # view + edit only
VIEW_ONLY = [T, F, F, F, F]  # view only
NO_ACCESS = [F, F, F, F, F]  # no access at all

MATRIX = {
	# ── ADMIN / SUPER / DIRECTOR / MANAGER / GENERAL-MANAGER ──────────
	"Administrator": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"Superadmin": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"Director": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"Manager": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"General Manager": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"Accounts Manager": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── ACCOUNTS-STAFF (scheduling=view+edit, ohs=no access) ──────────
	"Accounts Staff": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": VIEW_EDIT,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── ACCOUNTS (scheduling full, ohs=no access) ─────────────────────
	"Accounts": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── ACCOUNT ASSISTANT (same as accounts) ──────────────────────────
	"Account Assistant": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"Accounts User": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	"Enviro Accounts": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── OPERATIONS MANAGER ────────────────────────────────────────────
	"Operations Manager": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── OPERATIONS ASSISTANCE MANAGER (ohs=no access) ─────────────────
	"Operations Assistance Manager": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── SUPERVISOR (scheduling view+edit, ohs=no access) ──────────────
	"Supervisor": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": VIEW_EDIT,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── SCHEDULER (team=view+edit, ohs full) ──────────────────────────
	"Scheduler": {
		"team": VIEW_EDIT,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── SALES STAFF ──────────
	"Sales Staff": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── SALES MANAGER ───────────────────────────────────
	"Sales Manager": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── SALES PUMPS (very limited — home/sales/accounts/invoice only) ─
	"Sales Pumps": {
		"team": NO_ACCESS,
		"site": NO_ACCESS,
		"home": FULL,
		"vehicle": NO_ACCESS,
		"sales": FULL,
		"scheduling": NO_ACCESS,
		"ohs": NO_ACCESS,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── PUMP MANAGER ──────────────────────────────────────────────────
	"Pump Manager": {
		"team": VIEW_ONLY,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── PUMP COORDINATOR ──────────────────────────────────────────────
	"Pump Coordinator": {
		"team": VIEW_ONLY,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── PUMP TECHNICIAN (team=no, sales=view+edit, ohs=view+edit) ─────
	"Pump Technician": {
		"team": NO_ACCESS,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": VIEW_EDIT,
		"scheduling": FULL,
		"ohs": VIEW_EDIT,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── TECHNICAL MANAGER (team=no) ───────────────────────────────────
	"Technical Manager": {
		"team": NO_ACCESS,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── WHS MANAGER (team=no) ─────────────────────────────────────────
	"Whs Manager": {
		"team": NO_ACCESS,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── FACTORY MANAGER (team=no) ─────────────────────────────────────
	"Factory Manager": {
		"team": NO_ACCESS,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── GMS ASSISTANT (full access all) ───────────────────────────────
	"Gms Assistant": {
		"team": FULL,
		"site": FULL,
		"home": FULL,
		"vehicle": FULL,
		"sales": FULL,
		"scheduling": FULL,
		"ohs": FULL,
		"intranet": FULL,
		"accounts": FULL,
		"invoice": FULL,
	},
	# ── ALL ROUNDER (view-only on team/site/home/intranet, rest=none) ─
	"All Rounder": {
		"team": VIEW_ONLY,
		"site": VIEW_ONLY,
		"home": VIEW_ONLY,
		"vehicle": NO_ACCESS,
		"sales": NO_ACCESS,
		"scheduling": NO_ACCESS,
		"ohs": NO_ACCESS,
		"intranet": VIEW_ONLY,
		"accounts": NO_ACCESS,
		"invoice": NO_ACCESS,
	},
	# ── DRIVER LIQUID WASTE TECHNICIAN (MOBILE) ───────────────────────
	"Driver Liquid Waste Technician (Mobile)": {
		"team": NO_ACCESS,
		"site": NO_ACCESS,
		"home": VIEW_ONLY,
		"vehicle": VIEW_ONLY,
		"sales": NO_ACCESS,
		"scheduling": VIEW_ONLY,
		"ohs": VIEW_ONLY,
		"intranet": VIEW_ONLY,
		"accounts": NO_ACCESS,
		"invoice": NO_ACCESS,
	},
	# ── DRIVER LIQUID WASTE TECHNICIAN (WEB) ─────────────────────────
	"Driver Liquid Waste Technician (Web)": {
		"team": NO_ACCESS,
		"site": NO_ACCESS,
		"home": VIEW_ONLY,
		"vehicle": VIEW_ONLY,
		"sales": NO_ACCESS,
		"scheduling": VIEW_ONLY,
		"ohs": VIEW_ONLY,
		"intranet": VIEW_ONLY,
		"accounts": NO_ACCESS,
		"invoice": NO_ACCESS,
	},
	# ── DRIVER FACTORY HAND (MOBILE) ─────────────────────────────────
	"Driver Factory Hand (Mobile)": {
		"team": NO_ACCESS,
		"site": NO_ACCESS,
		"home": VIEW_ONLY,
		"vehicle": VIEW_ONLY,
		"sales": NO_ACCESS,
		"scheduling": VIEW_ONLY,
		"ohs": VIEW_ONLY,
		"intranet": VIEW_ONLY,
		"accounts": NO_ACCESS,
		"invoice": NO_ACCESS,
	},
	# ── DRIVER FACTORY HAND (WEB) ────────────────────────────────────
	"Driver Factory Hand (Web)": {
		"team": NO_ACCESS,
		"site": NO_ACCESS,
		"home": VIEW_ONLY,
		"vehicle": VIEW_ONLY,
		"sales": NO_ACCESS,
		"scheduling": VIEW_ONLY,
		"ohs": VIEW_ONLY,
		"intranet": VIEW_ONLY,
		"accounts": NO_ACCESS,
		"invoice": NO_ACCESS,
	},
}

# Workspace name mapping (module key → Workspace doc name)
WORKSPACE_MAP = {
	"team": "Team",
	"site": "Sites",
	"home": "Home",
	"vehicle": "Vehicles",
	"sales": "Sales",
	"scheduling": "Scheduling",
	"ohs": "OH & S",
	"intranet": "Intranet",
	"accounts": "Accounts",
	"invoice": "Invoice",
}

# Core DocTypes that receive role-level CRUD custom permissions
# We map each workspace module to its primary DocType
DOCTYPE_MAP = {
	"team": [],
	"site": ["Site", "Site Document", "Site Waste Profile"],
	"vehicle": ["Vehicle"],
	"sales": [
		"Quotation",
		"Customer",
		"Enviro Job Card",
		"Territory",
		"Waste Type",
		"Accounts Settings",
		"Selling Settings",
	],
	"scheduling": ["Enviro Job", "Enviro Job Team Member"],
	"invoice": ["Sales Invoice"],
}


def _clear_workspace_roles(ws_name):
	if frappe.db.exists("Workspace", ws_name):
		ws = frappe.get_doc("Workspace", ws_name)
		ws.set("roles", [])
		ws.save(ignore_permissions=True)


def apply_workspace_visibility():
	"""Step 1: set roles on each Workspace doc based on View column."""
	# Build inverse map: workspace → list of roles that have view=True
	ws_roles = {v: [] for v in WORKSPACE_MAP.values()}

	for role, modules in MATRIX.items():
		if not frappe.db.exists("Role", role):
			continue
		for mod_key, perms in modules.items():
			view = perms[0]
			ws_name = WORKSPACE_MAP.get(mod_key)
			if ws_name and view:
				ws_roles[ws_name].append(role)

	# Apply to Workspace docs
	for ws_name, roles in ws_roles.items():
		if not frappe.db.exists("Workspace", ws_name):
			print(f"  SKIP (not found): {ws_name}")
			continue
		ws = frappe.get_doc("Workspace", ws_name)
		ws.set("roles", [])
		for role in roles:
			ws.append("roles", {"role": role})

		ws.save(ignore_permissions=True)
		print(f"  Workspace '{ws_name}': {len(roles)} roles applied")


def apply_doctype_permissions():
	"""Step 2: set Custom DocPerm records for core DocTypes."""
	for mod_key, doctypes in DOCTYPE_MAP.items():
		for doctype in doctypes:
			# Remove existing custom perms to start fresh
			frappe.db.delete("Custom DocPerm", {"parent": doctype})

			for role, modules in MATRIX.items():
				if not frappe.db.exists("Role", role):
					continue
				perms = modules.get(mod_key, NO_ACCESS)
				view, add, edit, delete, pre_insp = perms

				if not view:
					continue  # no read = skip (role simply has no access)

				# Build the custom perm row
				perm = frappe.new_doc("Custom DocPerm")
				perm.parent = doctype
				perm.parenttype = "DocType"
				perm.parentfield = "permissions"
				perm.role = role
				perm.permlevel = 0
				perm.read = 1
				perm.write = 1 if edit else 0
				perm.create = 1 if add else 0
				perm.delete = 1 if delete else 0
				perm.submit = 1 if pre_insp else 0
				perm.cancel = 1 if pre_insp else 0
				perm.amend = 1 if pre_insp else 0
				perm.insert()

			print(f"  DocType '{doctype}': custom perms applied")

	frappe.db.commit()


def apply_all():
	"""Run both steps and clear caches."""
	print("=== Step 1: Workspace visibility ===")
	apply_workspace_visibility()

	print("\n=== Step 2: DocType permissions ===")
	apply_doctype_permissions()

	frappe.clear_cache()
	print("\nDone. Cache cleared.")
