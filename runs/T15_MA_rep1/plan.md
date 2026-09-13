## Plan

**1. Files I expect to touch:**
- `src/click/core.py` — likely location of the option help-record/default-display logic (e.g., `Option.get_help_record` method that formats the default value for display in `--help` output).
- `CHANGES.rst` — add changelog entry summarizing the fix and linking to issue #2500.
- Possibly a docs file if default-value display behavior is documented (e.g., in `docs/options.rst`), but only if inaccurate docs are found.

**2. Steps in order:**
1. Locate the code responsible for computing/displaying the "default" annotation in help text — search `core.py` for where `show_default` is handled and where the default value is converted to a string (likely a truthiness check like `if default_value:` which would fail for empty string `""`).
2. Confirm the bug: an empty string default (`default=""`) is falsy in Python, so the current condition likely skips showing `(default: )` or omits it entirely, even when `show_default=True`.
3. Modify the condition to explicitly check `default_value is not None` (or similar) instead of relying on truthiness, so that empty strings are still displayed as defaults.
4. Verify formatting: ensure an empty string default renders as `(default: '')` or an appropriate empty representation, consistent with existing tests already in the repo.
5. Run the existing test suite (particularly tests related to `test_options.py` or `test_basic.py` covering `show_default` and default rendering) to confirm the fix resolves the failing test(s) without modifying test files.
6. Add a `CHANGES.rst` entry under the appropriate unreleased version section, referencing issue #2500 and PR #2724.
7. Check inline docstrings/comments near the modified code for `.. versionchanged::` markers; add one if the project convention requires documenting behavior changes in the `Option` class docstring.
8. Re-run full test suite to confirm no regressions elsewhere (e.g., defaults that are `None`, `False`, `0`, or empty collections should retain correct prior behavior).

**3. Risks or things I'm unsure about:**
- Need to distinguish between "no default was set" (`None`) vs. "default is falsy but valid" (`""`, `0`, `False`, `[]`) — must ensure fix doesn't break existing behavior for `None` defaults (which should still hide the default) or other falsy-but-meaningful defaults like `0`/`False` (which may already work correctly and shouldn't be altered further).
- The exact display format for an empty string default is unclear — need to check existing tests to see expected output (e.g., `(default: )` vs `(default: '')`) to match precisely.
- There may be multiple code paths (e.g., `Parameter.get_help_record`, `Option.get_help_record`, or a shared helper) that need the same fix — must search thoroughly to avoid missing a duplicate check elsewhere.
- Interaction with `show_default` parameter variants (`True`, a string override, or callable defaults via `default_factory`) — need to ensure the fix doesn't interfere with these other branches of the same logic.
- Should verify whether `flag` type options or `multiple`/`nargs>1` options with empty tuple/list defaults are affected differently and don't need separate handling.