## Plan

**1. Files I expect to touch**
- `src/click/decorators.py` — location of the `command()` decorator logic containing the `kwargs["cls"]` assignment and the `assert (len(args) == 1 and not kwargs)` check.
- `CHANGES.rst` — add changelog entry referencing issue #2416.
- Possibly `.. versionchanged::` docstring update within `decorators.py` (docs are inline, not a separate file).

**2. Steps in order**
1. Locate the `command()` decorator in `src/click/decorators.py` and inspect the current order of operations:
   - Setting `kwargs["cls"] = kwargs.get("cls", Command)` (or similar, using `self.command_class` if applicable).
   - The assertion `assert (len(args) == 1 and not kwargs)` used to detect the case where `@command` is used directly as a decorator (no parentheses) on a function.
2. Identify why parameterless usage fails when a custom `command_class` is set: the `cls` key gets injected into `kwargs` *before* the assertion checks `not kwargs`, causing the assertion to fail even though the user passed no explicit arguments.
3. Reorder the logic so that:
   - The assertion for "parameterless usage" (`len(args) == 1 and not kwargs`) is evaluated first, based on the *original* args/kwargs passed by the caller.
   - Only after determining whether it's the parameterless form, inject `kwargs["cls"]` (or resolve `cls`) as needed for the actual command construction.
4. Ensure this reordering does not break the parameterized usage (`@command(cls=CustomClass)` or `@group()`), i.e., `cls` resolution should still work correctly when arguments are passed.
5. Re-run existing test suite (without modifying test files) to confirm the already-present tests for this issue now pass.
6. Add a `.. versionchanged::` note in the `command()` (and possibly `group()`) docstring describing the fix for parameterless usage with custom `cls`.
7. Add a `CHANGES.rst` entry summarizing the fix and linking to issue #2416.
8. Run `pre-commit` (formatting/lint) and `pytest`/`tox` locally to confirm no regressions.

**3. Risks / Uncertainties**
- Need to check both `command()` and `group()` decorators — the fix likely applies to both since `group()` often delegates to `command()` internals or has parallel logic; must confirm code structure to avoid missing one.
- The reordering must preserve behavior for other edge cases, e.g., calling `@command(name="foo")` with a custom class, or calling `@command` with positional function argument plus `cls` in kwargs (invalid combination) — need to make sure assertion still correctly rejects invalid combinations.
- Must not alter the public API or signature, only internal ordering — must verify no side effects on subclasses overriding `command_class`.
- Should verify whether `self.command_class` (on `Group`) attribute interacts with `kwargs["cls"]` default assignment, since this could affect the reordering logic in more complex ways.
- Existing tests should be treated as ground truth (do not modify), so the implementation must be crafted to satisfy them exactly — need to carefully re-derive expected behavior from test names/assertions.
- Small risk of breaking backward compatibility if some users relied on the previous (buggy) assertion ordering, though this is unlikely given it's a bug fix.