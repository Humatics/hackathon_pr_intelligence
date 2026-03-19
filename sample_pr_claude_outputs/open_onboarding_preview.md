## 1. Summary

Adds a new `get_onboarding_preview` API endpoint that delegates to `build_onboarding_packet` in the workflows layer, with a demo call in `main.py`.

## 2. Risk Level

**High** — Preview endpoint likely triggers real notification and billing side effects (called out explicitly in the review guide and the PR's own open questions), and ships with zero automated tests.

## 3. Checklist

| Item | Status | Note |
|------|--------|------|
| Null safety on `values` | ⚠️ | No visible guard before `values` reach downstream aggregations (`max`, percentile); relies entirely on `build_onboarding_packet` internals we can't verify from this diff |
| Null safety on user email | ❌ | Guide warns onboarding preview hits notification code; no evidence user-email-is-None path (user 43) is handled |
| Test coverage | ❌ | PR states "automated tests still TODO" — guide requires happy-path, empty/None, boundary, and missing-field tests |
| API contract stability | ✅ | New function only; no existing signatures changed |
| Side effects in preview | ❌ | Guide §"Side Effects in Preview Endpoints" and §"Known Gaps → open_onboarding_preview" both flag that notification fires during preview. PR's own open question confirms this is unresolved |
| Data-flow structure | ❌ | `main.py` imports `build_onboarding_packet` directly from `workflows.py`, bypassing `api.py` — violates `main → api → services` flow |
| Return shape documented | ⚠️ | Docstring says "combined onboarding preview payload" but doesn't list expected dict keys per style guide |
| Retry logic scope | ⚠️ | Can't confirm from diff whether `build_onboarding_packet` wraps validation errors in `retry()` |
| `workflows.py` complexity | ⚠️ | Adding a new orchestration function is fine, but guide warns not to pile more logic into existing deep-nesting functions — can't verify from this diff |

## 4. Issues Found

1. **No tests (blocker)** — `tests/` has no new file or additions. The guide requires coverage for happy path, all-`None` values, `amount=0`, `percentile` boundaries, and users 43/45 (missing email/fields). → *all test files*

2. **Side effects in preview (blocker)** — `app/api.py:23`: `get_onboarding_preview` calls `build_onboarding_packet`, which per the guide fires real notifications and billing during preview. This must be verified side-effect-free or explicitly suppressed (e.g., `dry_run=True` flag) before merge.

3. **`main.py` bypasses API layer** — `app/main.py:4`: imports `build_onboarding_packet` directly from `app.workflows` instead of calling `api.get_onboarding_preview`. Should be:
   ```python
   from app.api import get_onboarding_preview
   ...
   print(get_onboarding_preview("44", [3, 4, 5], 19.99))
   ```

4. **Null-email crash path unaddressed** — If the onboarding packet builds a notification channel for a user with `email=None` (user 43), it will hit known bug #4 (`AttributeError` in `pick_delivery_channel`). No guard or test added.

5. **No input validation on `amount`** — PR's own open question ("should this endpoint tolerate invalid payment amounts?") is unanswered. Negative or zero `amount` behaviour is undefined and untested.

6. **Return shape undocumented** — `app/api.py:22`: docstring doesn't specify expected dict keys. Other endpoints in the file return explicit dicts with named keys; this one is an opaque passthrough with no contract.

## 5. Verdict

**Request Changes**

The two blocking issues — zero test coverage and unverified side effects in a preview endpoint — must be resolved before merge. The `main.py` import path and null-safety gaps are straightforward fixes that should come in the same revision.