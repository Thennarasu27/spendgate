## B2c — Dangerous Patterns

There are two bugs:
1. `self.save()` inside `validate()` is wrong because `validate()` is already called during save. It can cause a recursive save.

2. Changing `budget.total_allocated` directly is unsafe. If a claim is cancelled or edited, the stored value can become wrong. Two claims being edited at the same time can also cause incorrect values.

So SpendGate calculates the current spend using a live aggregate query instead of storing a running balance.

### Corrected version

```python
def validate(self):
    self.total_amount = sum(r.amount for r in self.expense_lines)

## B2d — The Race Condition Question

Yes, both submissions could succeed if both controllers calculate `spent_so_far` before either transaction commits. This is a TOCTOU race condition. The current live aggregate query does not by itself prevent this. Unless SpendGate uses a database lock/transaction mechanism such as `SELECT ... FOR UPDATE` on the Budget row, nothing currently protects against both requests passing the budget check at the same time.

## D2 - Data Leaks

frappe.get_all() ignores normal permission checks, so using it in a whitelisted method can expose Expense Claims to users without permission to access all claims.

frappe.get_list() is permission-aware and should be used for user-facing queries.
### E1 — on_update

Calling `doc.save()` inside `on_update()` causes `on_update()` to run again, which can create an infinite recursive save.
So we should not call `save()` inside `on_update()`.

###H1 — Async Pitfall

frappe.call() is asynchronous, so its result is not available immediately during the validate event.
validate must finish its checks synchronously before the form can be submitted.
Therefore, fetch budget data in onload/refresh and store the result for validate or field-change checks.

### J1 

Using `frappe.get_all()` directly in Jinja means the database query happens while the print format is rendering.
Using `before_print()` means the data is fetched in Python before rendering and stored in `doc.precomputed_field`.
Jinja then only displays the precomputed data.
This keeps database logic separate from the print template.

curl api - # thennarasu@Thennarasu:~/new-bench$ curl -X GET "http://127.0.0.1:8000/api/resource/Expense%20Claim" -H "Authorization: t
# oken fa162a06b788b95:78ef2212ed83826"
# {"data":[{"name":"EXP-2026-00001"},{"name":"EXP-2026-00002"},{"name":"EXP-2026-00003"},{"name":"EXP-2026-00004"},{"name":"EXP-2026-00005"},{"name":"EXP-2026-00006"},{"name":"EXP-2026-00007"}]}thennarasu@Thennarasu:~/new-bench$
#worked
