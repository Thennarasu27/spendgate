# curl -X GET "http://eval.local/api/resource/Expense%20Claim" \
#   -H "Authorization: token YOUR_API_KEY:YOUR_API_SECRET"

# thennarasu@Thennarasu:~/new-bench$ curl -X GET "http://127.0.0.1:8000/api/resource/Expense%20Claim" -H "Authorization: t
# oken fa162a06b788b95:78ef2212ed83826"
# {"data":[{"name":"EXP-2026-00001"},{"name":"EXP-2026-00002"},{"name":"EXP-2026-00003"},{"name":"EXP-2026-00004"},{"name":"EXP-2026-00005"},{"name":"EXP-2026-00006"},{"name":"EXP-2026-00007"}]}thennarasu@Thennarasu:~/new-bench$

import frappe

@frappe.whitelist()
def get_budget_status():
    budget_name = frappe.form_dict.get("budget_name")
    budget = frappe.db.get_value(
        "Budget",
        budget_name,
        ["allocated", "spent", "remaining", "utilization_percent"],
        as_dict=True
    )
    if not budget:
        frappe.local.response.http_status_code = 404
        return {"error": "Not found"}

    return {
        "allocated": budget.allocated,
        "spent": budget.spent,
        "remaining": budget.remaining,
        "utilization_percent": budget.utilization_percent
    }

from frappe.query_builder import DocType

#b2a - http://127.0.0.1:8000/api/method/spendgate.api.get_claims_pending_approval
@frappe.whitelist()
def get_claims_pending_approval():
    EC = DocType("Expense Claim")

    result = (
        frappe.qb.from_(EC)
        .select(
            EC.name,
            EC.employee,
            EC.department,
            EC.total_amount,
            EC.expense_date
        )
        .where(EC.status == "Pending")
        .orderby(EC.expense_date)
        .run(as_dict=True)
    )

    return result

#b2b - http://127.0.0.1:8000/api/method/spendgate.api.reassign_department_claims?from_dept=Training&to_dept=Marketing
@frappe.whitelist()
def reassign_department_claims(from_dept, to_dept):
    try:
        frappe.db.sql(
            """
            UPDATE `tabExpense Claim`
            SET department = %s
            WHERE department = %s
            AND docstatus = 0
            """,
            (to_dept, from_dept)
        )

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Reassign Department Claims")
        raise