# Plan: Fix propagation of `show_default` option to sub-commands

## 1. Files I expect to touch
- `src/click/core.py` — likely location of `Context` class and option/parameter handling logic where `show_default` is defined and propagated (e.g., `Context.__init__`, `Parameter.get_help_record`, or context inheritance logic).
- Possibly `CHANGES.rst` — to add a changelog entry documenting the fix (following click's convention).

I will NOT touch test files (e.g., `tests/test_context.py` or similar) since they already encode expected behavior.

## 2. Steps in order

1. **Reproduce/understand the bug**: Inspect issue #1565 context — likely that `show_default` set on a parent `Context` (or via `Context.show_default` attribute) is not inherited by child contexts created for sub-commands, causing `--help` output on sub-commands to not show defaults even when the parent context enabled it.

2. **Locate relevant code**: Search `src/click/core.py` for `show_default` usage — in `Context.__init__` (where it's likely stored as `self.show_default`), and in `Option.get_help_record` (where it checks `ctx.show_default`).

3. **Inspect context inheritance**: Look at `Context.__init__` parameters and how `parent` context values are inherited for other similar settings (e.g., `token_normalize_func`, `color`, `max_content_width`) to see the established pattern for propagating settings from parent to child context when not explicitly set.

4. **Identify the bug**: Likely `show_default` defaults to `False` unconditionally instead of falling back to `parent.show_default` when not explicitly passed, breaking propagation to sub-command contexts.

5. **Run failing tests**: Locate and run the pre-existing test(s) related to this issue (likely in `tests/test_context.py` or `tests/test_options.py`) to confirm current failure and understand exact expected behavior/API.

6. **Implement fix**: Modify `Context.__init__` so that if `show_default` is `None` (or not explicitly given), it inherits from `parent.show_default` if a parent exists, otherwise defaults to `False`. This mirrors the existing pattern used for other inherited context attributes.

7. **Verify default value handling**: Ensure the default parameter value for `show_default` in `Context.__init__` signature is changed to `None` (instead of `False`) so it can distinguish "not set" from "explicitly False", enabling correct inheritance logic.

8. **Check `Command.make_context` / `Command.invoke`**: Confirm sub-command context creation passes `parent=self` correctly, and that no other place overrides `show_default` incorrectly.

9. **Run full test suite**: Run `tests/` to ensure the pre-existing test(s) for this issue now pass and no other tests regress (particularly `test_context.py`, `test_options.py`, `test_basic.py`).

10. **Update changelog**: Add an entry to `CHANGES.rst` describing the fix, referencing issue #1565 / PR #1566.

11. **Final review**: Double check diff is minimal, only touches `core.py` (and changelog), and doesn't modify any test files.

## 3. Risks / Uncertainties

- **Distinguishing "unset" vs "explicitly False"**: Changing default from `False` to `None` in `Context.__init__` signature could have subtle side effects if `show_default` is read elsewhere assuming a boolean (e.g., `if ctx.show_default:` still works fine with `None`, but explicit `is True`/`is False` checks elsewhere could break).
- **Backward compatibility**: Any external code or internal code that directly constructs `Context` with `show_default=False` as an explicit default might change behavior once inheritance logic is added — need to ensure this doesn't break other tests.
- **Multiple attributes with similar pattern**: Need to be careful to only change `show_default`, not accidentally alter propagation logic for unrelated settings.
- **Interaction with `Option.show_default`**: There may be two separate places (`Context.show_default` global setting and `Option(show_default=...)` per-parameter) — must ensure the fix targets the right one (context-level propagation, not per-option attribute).
- **Test file location unknown**: Since test files "already present" per instructions, I need to locate the exact test file/test name tied to this issue without modifying it, to correctly infer expected API/behavior.
- **CHANGES.rst conflicts**: Minor risk of merge/format issues when adding changelog entry if the format has strict conventions.