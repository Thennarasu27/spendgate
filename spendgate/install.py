import frappe
def after_install():
    departments = [
        "Engineering",
        "Finance",
        "HR",
        "Training",
    ]
    categories = [
        "Travel",
        "Software & Equipment",
        "Client Entertainment",
        "Training",
    ]
    for name in departments:
        if not frappe.db.exists("Department", name):
            frappe.get_doc({
                "doctype": "Department",
                "department_name": name
            }).insert(ignore_permissions=True)

    for name in categories:
        if not frappe.db.exists("Expense Category", name):
            frappe.get_doc({
                "doctype": "Expense Category",
                "category_name": name
            }).insert(ignore_permissions=True)

    if not frappe.db.exists("SpendGate Settings"):
        frappe.get_doc({
            "doctype": "SpendGate Settings"
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.msgprint("SpendGate installed successfully with default data.")