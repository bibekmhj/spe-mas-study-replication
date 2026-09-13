# Plan

## 1. Files I expect to touch
- `src/click/testing.py` — main fix location, likely in `CliRunner.invoke()` where `SystemExit`/`ctx.exit()` is caught; need to ensure the context is closed (callbacks invoked) before returning the `Result`.
- `src/click/core.py` — possibly need to expose/adjust `Context.close()` behavior or ensure `ctx.exit()` triggers closing properly (e.g., in `BaseCommand.main()` or `Context.exit()`), add `.. versionchanged::` docstring entries.
- `CHANGES.rst` — add changelog entry linking to issue/PR #2680.
- Documentation files (e.g., `docs/testing.rst` or relevant docstrings) — note behavior of context closing on exit, if applicable.

(Test files already present, not to be modified.)

## 2. Steps in order
1. **Reproduce the failure**: Run the existing (pre-supplied) failing tests to understand exact expected behavior — likely a test that registers a callback via `ctx.call_on_close()` or an option's callback, then calls `ctx.exit()`, and asserts the callback was invoked.
2. **Locate the exit-handling code path**: Inspect `click.testing.CliRunner.invoke()` to find where `SystemExit` is caught after invoking the command, and check whether `ctx.close()` is called there or only implicitly via context manager `__exit__`.
3. **Inspect `Context.exit()`/`Context.close()`/`BaseCommand.main()`** in `core.py` to see how normal (non-exception) exits handle context closing versus exception-triggered exits (`SystemExit`).
4. **Identify the gap**: Likely when `ctx.exit()` raises `SystemExit` inside `with self.make_context(...) as ctx:` block, the `__exit__` should call `ctx.close()`, but perhaps in `testing.py`'s manual invocation flow (which may not use the context manager the same way, or catches `SystemExit` before cleanup happens), the close is skipped.
5. **Implement fix**: Ensure that whenever `SystemExit` (or any exit path) occurs during invocation, `ctx.close()` is explicitly called — e.g., wrap invocation in `try/finally` in `testing.py`, or fix `main()` in `core.py` to guarantee context closing on all exit paths (normal, exception, `SystemExit`).
6. **Add `.. versionchanged::` docstring** entries near `Context.exit()`, `Context.close()`, or `CliRunner.invoke()` describing the fix.
7. **Update `CHANGES.rst`** with a bullet point referencing PR #2680, explaining the fix for callback closing on CLI exit.
8. **Update docs** (e.g., testing docs) if they describe context lifecycle, to mention that callbacks are now guaranteed to run on exit.
9. **Run the pre-existing tests** to confirm they now pass without modification.
10. **Run full test suite / pre-commit** mentally (or via instructions) to check no regressions — verify no other code relies on the old (buggy) behavior of skipping cleanup on exit.

## 3. Risks / Uncertainties
- **Double-closing contexts**: If `ctx.close()` is called both by the `with` statement's `__exit__` and again explicitly in the fix, callbacks could be invoked twice. Need to check `Context.close()` for idempotency (e.g., clearing `_close_callbacks` after running them) or guard against double-calls.
- **Scope of fix**: Unsure if the fix belongs in `testing.py` only, or if it also needs to apply to real CLI usage in `core.py`'s `main()`/`invoke()` for non-test scenarios (the PR emphasizes unit tests, but the actual bug might be in core exit handling that testing.py exposes).
- **Nested contexts**: Commands with subcommands/groups have nested `Context` objects; need to ensure closing the top-level context also closes/propagates to child contexts if callbacks were registered on children.
- **Interaction with `standalone_mode`**: `BaseCommand.main()` has a `standalone_mode` flag altering exception handling; need to check both standalone and non-standalone paths are fixed consistently.
- **Backward compatibility**: Some existing tests might implicitly rely on callbacks NOT running on early exit (unlikely, but worth checking) — could cause unrelated test breakage.
- **Where exactly `SystemExit` is raised vs caught**: `ctx.exit()` raises `SystemExit`; if user code catches `SystemExit` themselves before it propagates to `main()`, our fix in `main()` might not trigger — but this is likely out of scope per the PR's stated intent.