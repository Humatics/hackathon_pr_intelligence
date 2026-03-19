# Code Review Guide

This guide defines review standards for this codebase: a plain-Python user management and reporting system with no external dependencies and in-memory storage.

---

## Always Check

### Null Safety
- Any access to `user.email` **must** be guarded: `user.email is not None` before calling `.endswith()` or similar (see `notification_service.py:36` for the live example of this failing)
- Aggregations (`max`, `min`, `sorted`) **must** run on filtered input — call `filter_present(values)` before any built-in aggregate
- Any collection indexing **must** check `len > 0` first; percentile calculations must also clamp the index to `len - 1`

### Test Coverage
New code must have tests that cover:
- The happy path
- Empty or all-`None` input
- Boundary values (`percentile=0.0`, `percentile=1.0`, `amount=0`, etc.)
- Users with missing fields (no email, empty name, no tags) — seed data includes these at IDs 43 and 45

Existing test files: `tests/test_api.py`, `tests/test_utils.py`, `tests/test_user_service.py`, `tests/test_billing.py`, `tests/test_edge_cases.py`. Run with `python -m pytest tests/`.

### API Contracts
- The API layer (`api.py`) is a thin passthrough — errors from services propagate directly to callers with no wrapping. New endpoints should follow this pattern; don't add error-handling middleware unless the task explicitly requires it.
- Function signatures in `api.py` define the external contract. Changing parameter names or return dict keys is a breaking change — flag it in review.

### Side Effects in Preview Endpoints
- "Preview" or "dry-run" endpoints must not trigger real side effects. `get_onboarding_preview()` currently calls notification and billing code — any PR touching preview logic must verify no live sends or charges occur.

### Retry Logic Scope
- `retry()` in `utils.py` is designed for transient failures. It must **not** wrap validation errors (`ValueError`) — retrying a known-bad input wastes cycles. Check that retry call sites only wrap I/O-like operations.

---

## Coding Style and Patterns

### Structure
- Data flows: `main.py` → `api.py` → services → `utils.py`. No circular imports.
- Services call `utils.py` helpers; they do not call each other except through `workflows.py` (the designated orchestration layer).
- `utils.py` functions are pure and stateless. Keep them that way — no service imports inside `utils.py`.

### Naming
- Functions use `snake_case`; use descriptive verbs: `build_`, `get_`, `send_`, `pick_`, `summarize_`.
- Avoid generic names (`buildThing`, `data`, `flag`, `mode`) — `legacy_helpers.py` is the negative example.
- Metric normalization belongs in one place; there is already a duplicate (`normalize_metric_name` appears in both `report_service.py` and `legacy_helpers.py`). Do not add a third copy.

### Defensive Helpers
Use the shared helpers in `utils.py` rather than reimplementing inline:
| Need | Use |
|------|-----|
| Filter `None` from a list | `filter_present(values)` |
| Average ignoring `None` | `average(values)` |
| Normalize a name | `normalize_name(name)` |
| Currency display | `format_currency(amount)` |
| Split comma-separated tags | `compact_tokens(value)` |
| Retry transient failures | `retry(operation, attempts, delay)` |

### Data Classes
`User`, `Order`, and `Notification` in `models.py` are plain dataclasses with no validation. Input validation belongs at the service boundary, not in the model. Do not add validation logic to models.

### Return Shapes
Service functions return plain dicts or dataclass instances — no custom response objects. Dict keys are string literals (e.g., `"count"`, `"average"`, `"status"`). New functions should follow the same pattern and document expected keys in a docstring.

---

## High-Risk Areas

### `report_service.py` — Data Aggregation
**Highest-risk file.** Contains three known bugs:
1. `build_daily_report()`: `max(values)` crashes on `None` — must use `max(filter_present(values))`
2. `build_percentile_report()`: `IndexError` on empty input — guard with `len(cleaned) > 0`
3. `build_percentile_report()`: off-by-one at `percentile=1.0` — clamp index to `len - 1`

Any PR touching this file must add regression tests for all three cases.

### `notification_service.py` — Null Email
`pick_delivery_channel()` crashes when `user.email is None` (user ID 43 in seed data). Every PR touching the notification flow must verify this path.

### `analytics.py` — Performance
`build_dashboard_data()` calls `get_user_summary()` twice per user and rebuilds the filtered metric list three times per user. `build_hot_path()` sorts inside a loop. PRs in this file should not make the redundancy worse; ideally they fix it.

### `workflows.py` — Complexity
`process_user_lifecycle()` nests 6 levels deep and mixes validation, transformation, control flow, and response formatting. Do not add more branches or optional flags to this function. If new behavior is needed, extract it into a helper first.

### `legacy_helpers.py` — Do Not Extend
This file is a designated refactoring target. Do not add new functions here. Do not import from it in new code. If a PR needs metric normalization, use `report_service.normalize_metric_name` (or consolidate the duplicate first).

### Sample PRs — Known Gaps
The open PRs in `sample_pr/` have documented gaps:
- `open_onboarding_preview`: missing null checks; notification fires as a side effect during preview
- `open_blank_cleanup`: placeholder with no content — reject until changes are ready

---

## Skip in Review

These files/directories exist for demonstration and should not be reviewed for code quality:

```
legacy_helpers.py          # Intentionally poor quality; refactoring target only
logs/                      # Error log samples for debugging exercises
sample_pr/                 # Example PR diffs for PR-intelligence exercises
notes/                     # Sprint notes; not production artifacts
README.md                  # Hackathon prompts; not project documentation
```

Do not flag issues in `legacy_helpers.py` as review comments — they are intentional and known.

---

## Quick Reference: Known Bugs

| # | Location | Trigger | Impact |
|---|----------|---------|--------|
| 1 | `report_service.py` `build_daily_report()` | `None` in values | `TypeError` on `max()` |
| 2 | `report_service.py` `build_percentile_report()` | Empty / all-None input | `IndexError` |
| 3 | `report_service.py` `build_percentile_report()` | `percentile=1.0` | `IndexError` off-by-one |
| 4 | `notification_service.py` `pick_delivery_channel()` | User with `email=None` | `AttributeError` |

These are intentionally unfixed. A PR that touches the surrounding code must not make them worse; a PR that explicitly fixes one must include a regression test.
