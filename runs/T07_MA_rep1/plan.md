## Plan

### 1. Files expected to touch
- `src/click/types.py` — locate `FuncParamType.convert()` and update its `except ValueError` handling to use the caught exception's message.
- `CHANGES.rst` (or equivalent changelog file) — add an entry referencing the fix and issue/PR number, if the project convention requires it.
- No test files should be modified (per instructions, tests already exist).

### 2. Steps in order
1. Locate `FuncParamType` class in `src/click/types.py` and inspect its `convert()` method to see how `ValueError` is currently caught and how `self.fail()` is called.
2. Modify the `except ValueError as e:` block:
   - Extract the exception message via `str(e)`.
   - If the message is non-empty, pass it to `self.fail(...)`.
   - If the message is empty (fallback for backward compatibility), pass the original `value` as before.
3. Ensure the rest of the arguments to `self.fail()` (param, ctx) remain unchanged.
4. Run the existing regression test (already present in the repo) to confirm the new behavior passes, e.g. `pytest tests/ -k FuncParamType` or the specific test file referenced in the PR.
5. Run the full test suite to ensure no regressions elsewhere (other types relying on `FuncParamType.convert()` behavior, e.g. custom callables used as types).
6. Update `CHANGES.rst` with a short note describing the fix and linking to issue #3105 / PR #3211, following existing changelog formatting conventions.
7. Review diff for style consistency (line length, quotes, etc.) matching the project's linting rules (flake8/black config).

### 3. Risks / open questions
- Need to confirm exact current implementation of `FuncParamType.convert()` — the exact except block and `self.fail()` call signature must match precisely to apply a minimal correct patch.
- Must verify how `self.fail()` builds its message string (e.g., does it already include `value`? Need to avoid duplicating value in the message when using the ValueError text).
- Should check whether other custom `ParamType` subclasses that raise `ValueError` inside callables might already provide meaningful messages — verify no double-wrapping of value occurs (e.g., message like `"'foo' is not a valid ...: original error"`).
- Confirm empty-message fallback logic: `str(e)` could be empty string for exceptions created via `ValueError()` with no args — need correct falsy check (`if message:` vs `if e.args:`).
- Ensure changelog format matches other entries (may not be required if not enforced by test suite, but good practice).
- Double check regression test location/name to run it without modifying it, to avoid accidentally altering test files.