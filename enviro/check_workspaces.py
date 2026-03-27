import frappe

def execute():
    workspaces = frappe.get_all("Workspace", fields=["name", "title", "public", "is_hidden"])
    print(f"Found {len(workspaces)} workspaces:")
    for w in workspaces:
        if not w.is_hidden:
            print(f"- {w.name} (Public: {w.public})")
