// Copyright (c) 2026, Thennarasu M and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Expense Claim", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on("Expense Claim", {
    setup(frm) {
        frm.set_query("budget", () => {
            return {
                filters: {
                    department: frm.doc.department,
                    fiscal_year: frm.doc.fiscal_year,
                    quarter: frm.doc.quarter
                }
            };
        });
    },

    refresh(frm) {
        // Status indicator
        if (frm.doc.status === "Pending") {
            frm.dashboard.add_indicator("Pendingl", "orange");
        } else if (frm.doc.status === "Approved") {
            frm.dashboard.add_indicator("Approved", "green");
        } else if (frm.doc.status === "Reimbursed") {
            frm.dashboard.add_indicator("Reimbursed", "blue");
        }

        // Budget remaining
        if (frm.doc.budget) {
            frappe.call({
                method: "spendgate.api.get_budget_status",
                args: {
                    budget_name: frm.doc.budget
                },
                callback(r) {
                    if (r.message && !r.message.error) {
                        frm.dashboard.add_indicator(
                            "Budget Remaining: " + r.message.remaining,
                            "green"
                        );
                        frm._budget_remaining = r.message.remaining;
                    }
                }
            });
        }

        // Approve button
        if (
            frm.doc.status === "Pending" &&
            (
                frappe.user.has_role("SG Department Head") ||
                frappe.user.has_role("Finance Manager")
            )
        ) {
            frm.add_custom_button("Approve", () => {
                frm.set_value("status", "Approved");
                frm.save();
            });
        }
    }
});


frappe.ui.form.on("Expense Line", {
    amount(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        let total = 0;

        (frm.doc.expense_lines || []).forEach(r => {
            total += flt(r.amount);
        });

        frappe.model.set_value(
            cdt,
            cdn,
            "amount",
            flt(row.amount)
        );

        frm.set_value("total_amount", total);

        if (
            frm._budget_remaining !== undefined &&
            total > frm._budget_remaining
        ) {
            frappe.msgprint(
                "Warning: Expense total exceeds the remaining budget."
            );
        }
    }
});