## Plan

**1. Files I expect to touch**
- `src/click/decorators.py` — location of the `command()` decorator logic that sets `kwargs["cls"]` and performs the `assert (len(args) == 1 and not kwargs)` check.
- `CHANGES.rst` — add changelog entry referencing issue #2416.
- Possibly `docs/` — if `command()` docstring contains `.. versionchanged::` notes that need updating, though test files are already present and should not be touched.

**2. Steps in order**
1. Locate the `command()` decorator implementation in `src/click/decorators.py` and identify the exact block where `kwargs.setdefault("cls", ...)` (or similar) is set and where the assertion `len(args) == 1 and not kwargs` is performed.
2. Analyze the current order of operations: currently `kwargs["cls"]` is likely set (via `self.command_class` or default) *before* the assertion checks whether `kwargs` is empty, which causes the assertion to fail incorrectly when a class-based decorator (e.g. a `Group` subclass with `command_class` set) is used with no arguments and a parameterless constructor is expected.
3. Reorder the logic so that the assertion for "used without parentheses" (`len(args) == 1 and not kwargs`) is evaluated *before* `kwargs["cls"]` is injected, ensuring that setting `cls` internally doesn't interfere with detecting the parameterless-decorator usage pattern.
4. Verify that when `self.command_class` is defined and the decorator is used as `@group.command` (no parens, no args), the assertion still correctly identifies this case and doesn't spuriously fail due to `cls` being added to `kwargs` beforehand.
5. Run existing tests in the test suite (already present, not to be modified) to confirm the fix resolves the failure described in #2416.
6. Add a `.. versionchanged::` note in the docstring of `command()` (and `group()` if affected) describing the fix.
7. Add an entry to `CHANGES.rst` summarizing the fix and linking to issue #2416.
8. Run `pre-commit` hooks (formatting/linting) and `pytest`/`tox` to ensure no regressions.

**3. Risks or things I'm unsure about**
- Need to confirm whether `group()` decorator has analogous logic duplicated separately from `command()`, requiring the same fix in two places.
- Reordering logic must not break the existing behavior for legitimate parameterized usage (e.g., `@command(cls=SomeClass)` or `@command("name", cls=SomeClass)`).
- Must ensure the fix doesn't affect other subclasses that override `command_class`/`group_class` with `None` vs. a real class — edge cases around `None` sentinel values need care.
- Should double check that no other call sites (e.g., `Group.command`, `Group.group`) have similar duplicated logic that also needs reordering.
- Must avoid touching the pre-existing test files per instructions, only modify source and docs/changelog.