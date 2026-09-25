frappe.ui.form.on("Expense Claim", {
    refresh(frm) {
        // Status indicator
        if (frm.doc.status === "Approved") {
            frm.dashboard.add_indicator("Approved", "green");
        } else if (frm.doc.status === "Pending Approval") {
            frm.dashboard.add_indicator("Pending Approval", "orange");
        } else if (frm.doc.status === "Rejected") {
            frm.dashboard.add_indicator("Rejected", "red");
        } else if (frm.doc.status === "Reimbursed") {
            frm.dashboard.add_indicator("Reimbursed", "green");
        } else {
            frm.dashboard.add_indicator(frm.doc.status || "Draft", "blue");
        }


        // Approve button
        if (
            frm.doc.status === "Pending" &&
            (
                frappe.user.has_role("SG Department Head") ||
                frappe.user.has_role("SG Finance Manager")
            )
        ) {
            frm.add_custom_button("Approve", function () {
                frappe.call({
                    method: "spendgate.expense_claim_api.approve_claim",
                    args: {
                        claim_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            });
        }

        // H2 buttons
        if (!frm.is_new()) {
            frm.add_custom_button("Reject Claim", function () {
                show_reject_dialog(frm);
            });

            frm.add_custom_button("Reassign Department", function () {
                reassign_department(frm);
            });
        }
    },
    department(frm) {
        // Re-run budget filtering/status when department changes
        frm.set_query("budget", function () {
            return {
                filters: {
                    department: frm.doc.department,
                    fiscal_year: frappe.defaults.get_user_default("fiscal_year")
                }
            };
        });

        load_budget_status(frm);
    },
    validate(frm) {
        // Client-side warning only.
        // Do NOT use frappe.call here because it is asynchronous.
        if (
            frm.doc.total_amount &&
            frm.doc.remaining_budget !== undefined &&
            frm.doc.total_amount > frm.doc.remaining_budget
        ) {
            frappe.msgprint({
                title: "Budget Warning",
                message: "This claim exceeds the remaining budget.",
                indicator: "orange"
            });
        }
    }
});
frappe.ui.form.on("Expense Line", {
    amount(frm, cdt, cdn) {
        let total = 0;

        (frm.doc.expense_line || []).forEach(row => {
            total += flt(row.amount);
        });

        frappe.model.set_value(
            frm.doctype,
            frm.doc.name,
            "total_amount",
            total
        );

        if (
            frm.doc.remaining_budget !== undefined &&
            total > frm.doc.remaining_budget
        ) {
            frappe.msgprint({
                title: "Budget Warning",
                message:
                    "Running total (" +
                    format_currency(total) +
                    ") exceeds the remaining budget (" +
                    format_currency(frm.doc.remaining_budget) +
                    ").",
                indicator: "orange"
            });
        }
    }
});
function load_budget_status(frm) {
    if (!frm.doc.budget) {
        frm.dashboard.clear_comment();
        return;
    }
    frappe.call({
        method: "spendgate.expense_claim_api.get_budget_status",
        args: {
            budget: frm.doc.budget
        },
        callback: function (r) {
            if (!r.message) {
                return;
            }
            let remaining = flt(r.message.remaining);
            frm.doc.remaining_budget = remaining;
            frm.dashboard.set_headline_alert(
                "Budget Remaining: " + format_currency(remaining),
                remaining > 0 ? "green" : "red"
            );
        }
    });
}
function show_reject_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: "Reject Claim",
        fields: [
            {
                fieldname: "rejection_reason",
                label: "Rejection Reason",
                fieldtype: "Small Text",
                reqd: 1
            }
        ],
        primary_action_label: "Reject",
        primary_action(values) {
            frappe.call({
                method: "spendgate.expense_claim_api.reject_claim",
                args: {
                    claim_name: frm.doc.name,
                    reason: values.rejection_reason
                },
                callback: function (r) {
                    if (!r.exc) {
                        dialog.hide();
                        frm.reload_doc();
                    }
                }
            });
        }
    });

    dialog.show();
}
function reassign_department(frm) {
    frappe.prompt(
        [
            {
                fieldname: "department",
                label: "Department",
                fieldtype: "Link",
                options: "Department",
                reqd: 1
            }
        ],
        function (values) {
            frappe.confirm(
                "Reassign this Expense Claim to " +
                values.department +
                "?",
                function () {
                    frappe.call({
                        method: "spendgate.expense_claim_api.reassign_department",
                        args: {
                            claim_name: frm.doc.name,
                            department: values.department
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                frm.reload_doc();
                                frm.trigger("department");
                            }
                        }
                    });
                }
            );
        },
        "Reassign Department",
        "Continue"
    );
}