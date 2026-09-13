## Test-Rationale Artifact

**Verdict: Adequate to demonstrate the fix, with minor follow-up recommended. Not a blocker for merge.**

### Does the test suite demonstrate the fix?

Yes, functionally. `test_propagate_show_default_setting` directly exercises the reported scenario:

1. A `Group` is created with `context_settings={"show_default": True}`.
2. A subcommand is invoked (`sub --help`), which builds a child `Context` via `Command.make_context`, passing `parent=<group's context>`.
3. The assertion `"[default: a]" in result.output` confirms the child context's help formatting picked up `show_default=True` from the parent — this is the exact end-to-end behavior the bug report concerns.

This is an integration-style test that validates the fix through the public CLI surface (`runner.invoke`), not just the internal attribute. That's a reasonable and idiomatic style for this codebase (consistent with other tests in `test_context.py`), and it does confirm the core inheritance logic works when wired through real command dispatch.

The full suite passing 20/20 with no other regressions is good signal that the change is backward-compatible.

### Gaps in coverage — worth adding before final sign-off

The single test only covers the "happy path" positive case. It does **not** verify:

1. **Explicit `False` at the parent is not clobbered** — i.e., a child context with `show_default=None` under a parent with `show_default=False` should show no default. Not strictly necessary since `False` is the pre-existing default, but worth a quick check given the reviewer's note about the `None` vs `False` sentinel distinction being load-bearing.
2. **Explicit override at the child** — a subcommand context constructed with `show_default=False` even though the parent has `show_default=True` should honor the child's explicit setting, not be overwritten. This is the most important missing case: it directly tests the `is None` guard that makes this fix correct rather than an unconditional inherit. Right now nothing in the diff proves this branch is guarded correctly other than code inspection.
3. **Multi-level nesting** (grandparent → parent → child) to confirm inheritance chains correctly, though this is lower priority since `Context.__init__` already resolves the value at construction time via `parent.show_default` (already-resolved value, not a lazy chain), so one level of nesting is representative enough.
4. A unit-level test directly on `Context` (constructing `Context(cmd, parent=parent_ctx)` and checking `.show_default`) would be faster and more precise than the CLI round-trip test, and would isolate the logic from help-formatting concerns (`[default: a]` string matching is somewhat indirect — a formatting regression elsewhere could mask a context-inheritance failure or vice versa).

### On the Reviewer's specific concerns

- **Signature default value (`None` vs `False`)**: This is a legitimate verification gap, but it is testable indirectly — the new test *passing* is strong evidence that `show_default` defaults to `None` on the child context (otherwise the `is None` branch would never fire and the test would fail with `AssertionError`). I'd consider this concern addressed by the passing test, though an explicit unit test asserting `Context(...).show_default is None` by default would make this self-documenting rather than inferred.
- **Test file modification against the plan's stated constraint**: This is a process/documentation issue, not a correctness issue. The test is well-written and appropriate; it should simply be called out in the PR description as an intentional, justified deviation (regression tests for bug fixes are standard practice and arguably should have been in-scope from the start).
- **Missing CHANGES.rst entry**: Cosmetic, does not block correctness, but should be added per project convention before merge.

### Recommendation

**Do not send back to Coder for the core fix** — it is correct and adequately demonstrated for the primary reported bug. However, I'd request one small addition before closing:

> Add a test case confirming that an explicit `show_default` on a child context (e.g., a subcommand or option declared with `show_default=False`) overrides an inherited `True` from a parent context. This directly tests the `is None` guard and removes any doubt about the sentinel logic being correct rather than coincidentally passing.

This is a fast, low-cost addition (a few lines, same pattern as the existing test) and would close the one real gap in coverage. Everything else (changelog entry) is housekeeping and can be handled in the same or a follow-up commit without re-opening the fix itself.