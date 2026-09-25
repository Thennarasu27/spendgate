import frappe

def validate(doc, method=None):
    for row in doc.expense_line:
        if row.amount <= 0:
            frappe.throw("Expense line amount must be greater than 0.")
    doc.total_amount = sum(row.amount for row in doc.expense_line)
    budget_department = frappe.db.get_value(
        "Budget",
        doc.budget,
        "department"
    )
    if doc.department != budget_department:
        frappe.throw("Expense Claim department must match Budget department.")

def before_submit(doc, method=None):
    budget = frappe.db.get_value(
        "Budget",
        doc.budget,
        ["total_allocated", "department"],
        as_dict=True
    )
    spent_so_far = frappe.db.sql("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM `tabExpense Claim`
        WHERE budget = %s
        AND docstatus = 1
        AND name != %s
    """, (doc.budget, doc.name))[0][0]
    remaining = float(budget.total_allocated) - float(spent_so_far)
    new_total = float(spent_so_far) + float(doc.total_amount)
    if new_total > float(budget.total_allocated):
        overage = new_total - float(budget.total_allocated)
        frappe.throw(
            f"Department {budget.department} exceeds the budget. "
            f"Overage: {overage}. "
            f"Budget remaining: {remaining}."
        )
    doc._remaining_budget = (
        float(budget.total_allocated) - new_total
    )

def on_submit(doc, method=None):
    doc.remaining_budget_at_submission = doc._remaining_budget
    if not doc.approved_by:
        doc.approved_by = frappe.session.user
    frappe.enqueue(
        "spendgate.expense_claim_api.notify_finance_of_new_claim",
        claim_name=doc.name
    )

def on_cancel(doc, method=None):
    if doc.status == "Reimbursed":
        frappe.throw(
            "Reimbursed claims cannot be cancelled."
        )
    doc.status = "Cancelled"

def on_trash(doc, method=None):
    if doc.status not in ["Draft", "Cancelled"]:
        frappe.throw(
            "Only Draft or Cancelled claims can be deleted."
        )

def on_update(doc, method=None):
    # Do not call doc.save() here.
    # It would trigger on_update again.
    pass