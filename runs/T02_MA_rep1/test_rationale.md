## Test Rationale: Double-Bracket Metavar Fix

### What the diff actually changes
`Argument.make_metavar()` used to unconditionally wrap the metavar in `[...]` whenever the argument was optional (`not self.required`). For types like `Choice` or `DateTime`, `get_metavar()` already returns a self-bracketed string (`[foo|bar|baz]`, `[%Y-%m-%d]`), so the wrapping produced `[[foo|bar|baz]]`. The fix adds a guard: skip re-wrapping if the metavar already starts with `[` and ends with `]`.

### Do the new tests demonstrate the fix?
Yes, reasonably well:

- `test_choice_argument_optional_metavar` covers both failure modes mentioned in the bug: `nargs=-1` (variadic) and `required=False` (optional), for a `Choice` argument. It asserts the correct single-bracket usage string *and* explicitly asserts the buggy double-bracket string is absent — a good "regression trap" pattern, since a naive fix that merely changed formatting without actually removing the duplication wouldn't satisfy the negative assertion.
- `test_datetime_argument_optional_metavar` confirms the fix generalizes beyond `Choice` to any type whose `get_metavar()` self-brackets (here `DateTime`), which is important because the guard in `core.py` is type-agnostic (string-shape based, not `isinstance` based). This is a meaningful second data point rather than a duplicate test.
- The full suite (90 tests) still passes, including `test_choice_argument_none`, which already exercised a *required* Choice argument's un-bracketed `{not-none|none}`-style metavar — so we have some assurance the fix doesn't affect the required-argument path. (Worth double-checking why that fixture uses `{}` and not `[]`; if `Choice.get_metavar` was also touched elsewhere it's outside this diff's scope, but confirm it's unrelated.)

### Gaps / suggestions for additional tests
Not blocking, but would strengthen confidence:

1. **Deprecated + optional combo**: In `make_metavar`, `var += "!"` is appended *before* the new bracket check. If a self-bracketing type is combined with `deprecated=True` and `required=False`, the metavar becomes `"[foo|bar]!"`, which no longer ends with `]`, so the guard fails to detect it's already bracketed, and the code would wrap it again into `"[[foo|bar]!]"`. This looks like a leftover edge case the fix doesn't address. It may be pre-existing/out-of-scope, but a test (or at least a Reviewer note) confirming expected behavior here would close the loop.
2. **`nargs > 1` (fixed arity) case**, e.g. `nargs=2`, not just `nargs=-1`, to confirm `"..."` suffix logic interacts correctly with the new guard.
3. A **plain non-bracketing type** (e.g., `IntParamType`) with `required=False` to explicitly pin down that the normal single-bracket wrapping path still functions — this is implicitly covered by other tests in the suite but not explicitly re-asserted alongside the new tests.
4. Ideally, a unit test calling `Argument.make_metavar()` directly (bypassing `--help` string matching) would make the intent clearer and less brittle to unrelated usage-string formatting changes, though the current CLI-level tests are acceptable given the codebase's existing testing style.

### Verdict
The fix and its tests are **adequate to merge**. The two added tests directly target the reported symptom (doubled brackets) across two different self-bracketing types, use precise negative assertions, and pass alongside the full pre-existing suite with no regressions. No hand-back to the Coder is required, but I'd suggest a lightweight follow-up test (or comment) addressing the `deprecated + optional` interaction noted above, since it's a plausible near-miss the current guard doesn't fully cover.