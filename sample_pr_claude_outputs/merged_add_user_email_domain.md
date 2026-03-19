## 1. Summary

Adds `get_user_email_domain(user_id)` to `user_service.py`, which looks up a user and returns the portion of their email after `@`.

## 2. Risk Level

**High** — The function will crash with `AttributeError` on any user whose `email` is `None` (e.g., seed-data user ID 43). This is the exact same class of bug documented for `notification_service.py:36`.

## 3. Checklist

| Item | Status | Note |
|---|---|---|
| Null Safety — `user.email` guard | ❌ | `user.email.split("@")` called without checking `user.email is not None`; crashes on user 43 |
| Null Safety — collection indexing | ⚠️ | `split("@")[1]` assumes `@` is present; malformed email causes `IndexError` |
| Test Coverage — happy path | ❌ | No tests added; PR explicitly states "manual smoke test only" |
| Test Coverage — `None` / missing fields | ❌ | No test for `email=None` (user 43) or empty name (user 45) |
| API Contracts | ✅ | No changes to `api.py` signatures or return shapes |
| Structure / data flow | ✅ | Helper lives in `user_service.py`, appropriate layer |
| Naming | ✅ | `get_user_email_domain` follows `get_` verb convention |
| Defensive helpers usage | ⚠️ | Could use `filter_present` or a guard pattern consistent with the rest of the codebase |
| No extension of `legacy_helpers.py` | ✅ | Not touched |
| Side effects | ✅ | Pure lookup, no side effects |

## 4. Issues Found

1. **`user_service.py:21` — `AttributeError` when `user.email is None`**
   `user.email.split("@")` will raise `AttributeError: 'NoneType' object has no attribute 'split'` for any user with a `None` email (user ID 43 in seed data). The review guide mandates a `user.email is not None` guard before any string operation on email.

   **Fix:**
   ```python
   def get_user_email_domain(user_id):
       user = get_user(user_id)
       if user is None:
           return None
       if user.email is None:
           return None
       return user.email.split("@")[1]
   ```

2. **`user_service.py:21` — `IndexError` on malformed email**
   If `user.email` exists but contains no `@` character, `split("@")` returns a single-element list and `[1]` raises `IndexError`. Defensive indexing or a length check is needed.

   **Fix (extending the above):**
   ```python
   parts = user.email.split("@")
   if len(parts) < 2:
       return None
   return parts[1]
   ```

3. **No unit tests**
   The review guide requires tests for: happy path, `None` email input, and boundary/missing-field users (IDs 43, 45). The PR ships zero tests. At minimum, `tests/test_user_service.py` needs:
   - Valid user → returns correct domain
   - Nonexistent user ID → returns `None`
   - User with `email=None` → returns `None` (not a crash)
   - (Optionally) malformed email → returns `None`

## 5. Verdict

**Request Changes** — The missing null check on `user.email` is a crash-path bug identical to the known `notification_service.py` issue, and there are no tests to catch it. Both must be addressed before merge.