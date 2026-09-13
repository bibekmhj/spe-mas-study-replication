## Plan

**1. Files expected to touch**
- `src/click/types.py` — modify `FuncParamType.convert()` to capture and use the `ValueError` message.
- `CHANGES.rst` — add changelog entry referencing the fix and issue/PR number.
- (No test files should be modified, per instructions; tests already exist to validate behavior.)

**2. Steps in order**
1. Locate `FuncParamType.convert()` in `src/click/types.py` and find the `except ValueError:` block that currently calls `self.fail(value, param, ctx)`.
2. Modify the except clause to capture the exception, e.g. `except ValueError as e:`.
3. Extract the message via `str(e)`.
4. If the message is non-empty, pass it to `self.fail(message, param, ctx)`; otherwise fall back to the original behavior (`self.fail(value, param, ctx)`) to preserve backward compatibility for exceptions with empty messages.
5. Run the existing/added regression test(s) (likely in `tests/test_types.py` or similar) to confirm the `BadParameter` exception now contains the ValueError message.
6. Run the full test suite to check for regressions in other tests relying on the old error format (e.g., tests checking `self.fail(value, ...)` output for built-in types like `int`, `float`, `bool`, `UUID`, etc., since many built-in converters raise bare `ValueError`).
7. Update `CHANGES.rst` with a short entry describing the fix and linking to the PR/issue.

**3. Risks or things to watch**
- Other built-in types (`INT`, `FLOAT`, `UUID`, `BOOL`, etc.) may rely on `FuncParamType.convert()` and currently produce error messages like `"'x' is not a valid integer."` derived from just the value. If their conversion functions raise `ValueError` with a message, the error text shown to users could change format — need to verify this doesn't break other tests asserting exact error strings.
- Need to ensure `str(e)` doesn't produce misleading text when the ValueError message itself doesn't include the original value (may need to check whether tests expect the value to still be included alongside the message, not just the message alone).
- Confirm behavior when `str(e)` is empty vs. non-empty — must correctly fall back without raising an unrelated exception.
- Double check that `self.fail()` signature and existing call sites remain consistent (fail expects a message string, not necessarily the value only).
- Do not touch pre-existing test files; only verify plan works against them, since they encode expected behavior.
- Check CHANGES.rst formatting/conventions used by the project (version heading, bullet style) to match existing entries.