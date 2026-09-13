# Plan: Fix propagation of `show_default` option to sub-commands

## 1. Files I expect to touch

- `src/click/core.py` — likely location of `Context` class and where `show_default` is defined/propagated (context settings inheritance logic).
- Possibly `src/click/decorators.py` — if `show_default` is set via decorators or option definitions that need to inherit context defaults.
- No test files will be modified (per instructions), but I will review:
  - `tests/test_context.py` or similar test file that likely contains the new/updated test cases for `show_default` propagation.

## 2. Steps in order

1. **Reproduce the issue**: Run the existing (already present) test(s) related to `show_default` propagation to confirm the failure and understand expected behavior.
2. **Locate `show_default` handling**: Search `core.py` for where `show_default` is defined as a `Context` parameter and how it's currently passed (or not passed) from parent `Context` to child `Context` when sub-commands are invoked.
3. **Inspect `Context.__init__`**: Check how other inheritable settings (e.g., `token_normalize_func`, `color`, `max_content_width`) are propagated from `parent` to child context, since `show_default` should likely follow the same pattern.
4. **Identify the bug**: Likely `show_default` is only checked via `self.show_default` without falling back to `parent.show_default` when not explicitly set on the child context (default value `None` vs `False` distinction may be the root cause).
5. **Implement fix**: Modify the `Context.__init__` (or wherever `show_default` is resolved) to inherit from `parent.show_default` when the child’s value is `None` (unset), mirroring the pattern used for other inherited context settings.
6. **Verify default value semantics**: Ensure `show_default` default is `None` (not `False`) at the `Context` level so inheritance can be distinguished from an explicit `False` set by the user.
7. **Run existing tests**: Execute the pre-existing test suite (especially the new tests for this issue) to confirm the fix resolves the failure without breaking other tests.
8. **Check formatting logic**: Confirm `Option.get_help_record` or wherever `show_default` is consumed reads from `ctx.show_default` correctly and respects the inherited value.
9. **Regression check**: Run full test suite to ensure no other context-inheritance behavior broke.

## 3. Risks / Uncertainties

- **Default value change**: Changing `show_default` default from `False` to `None` at the `Context` level could have subtle side effects wherever `show_default` truthiness is checked directly instead of via proper resolution — need to check all usages.
- **Interaction with `Command`-level `show_default`**: `show_default` can be set both at `Command`/`Option` level and `Context` level; need to make sure the fix doesn't conflate these two independent mechanisms.
- **Backward compatibility**: Users who explicitly pass `show_default=False` on a sub-command's context should not have it overridden by a parent's `True` — must preserve explicit `False` vs unset `None` distinction carefully.
- **Test files already present**: Since test files are already in place and must not be modified, I need to infer exact expected behavior solely from reading those tests, without assuming edge cases beyond what's tested.
- **Other inherited context params**: Should confirm consistency with how similar flags (e.g., `color`) are inherited to avoid introducing inconsistent patterns.