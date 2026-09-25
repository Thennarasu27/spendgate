import frappe

@frappe.whitelist()
def get_budget_status(budget):
    budget_doc = frappe.db.get_value(
        "Budget",
        budget,
        ["total_allocated", "department"],
        as_dict=True
    )
    if not budget_doc:
        frappe.throw("Budget not found.")
    spent = frappe.db.sql("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM `tabExpense Claim`
        WHERE budget = %s
        AND docstatus = 1
    """, (budget,))[0][0]
    remaining = float(budget_doc.total_allocated or 0) - float(spent or 0)
    return {
        "allocated": float(budget_doc.total_allocated or 0),
        "spent": float(spent or 0),
        "remaining": remaining,
        "department": budget_doc.department
    }

@frappe.whitelist()
def approve_claim(claim_name):
    if not (
        "SG Department Head" in frappe.get_roles()
        or "SG Finance Manager" in frappe.get_roles()
    ):
        frappe.throw("You are not allowed to approve claims.")
    doc = frappe.get_doc("Expense Claim", claim_name)
    if doc.status != "Pending":
        frappe.throw("Only Pending Approval claims can be approved.")
    doc.status = "Approved"
    doc.save()
    return {"status": "Approved"}

@frappe.whitelist()
def reject_claim(claim_name, reason):
    if not reason:
        frappe.throw("Rejection Reason is required.")
    doc = frappe.get_doc("Expense Claim", claim_name)
    doc.status = "Rejected"
    if doc.meta.has_field("rejection_reason"):
        doc.rejection_reason = reason
    doc.save()
    return {"status": "Rejected"}

@frappe.whitelist()
def reassign_department(claim_name, department):
    doc = frappe.get_doc("Expense Claim", claim_name)
    doc.department = department
    doc.save()
    return {"department": department}