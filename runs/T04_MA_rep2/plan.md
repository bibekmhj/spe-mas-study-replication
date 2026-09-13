# Plan

## 1. Files I expect to touch

- `src/click/testing.py` — likely location of `CliRunner.invoke()` where `SystemExit`/`ctx.exit()` is caught; need to ensure `ctx.close()` (or equivalent) is called before returning the result.
- `src/click/core.py` — the `BaseCommand.main()` method and/or `Context.exit()` method, where the exit exception is raised/handled; need to ensure context callbacks (`call_on_close` / `_close_callbacks`) are invoked even when exiting early via `ctx.exit()`.
- `CHANGES.rst` — add changelog entry referencing issue/PR #2680.
- Possibly `docs/` — update relevant documentation (e.g. docs on context callbacks, `ctx.exit()`, or `CliRunner`) with `.. versionchanged::` notes.

(Test files already exist and should not be modified.)

## 2. Steps in order

1. **Reproduce the bug**: Run the existing (already-present) failing tests to confirm the current behavior — callbacks registered via `ctx.call_on_close()` are not invoked when `ctx.exit()` is called.
2. **Trace the exit path**: Inspect `Context.exit()`, `BaseCommand.main()`, and `CliRunner.invoke()` to understand how `SystemExit`/`click.exceptions.Exit` propagates and where the context's `close()` is (or isn't) called.
3. **Identify the gap**: Determine whether `ctx.close()` is skipped when exit happens via `sys.exit()`/`ctx.exit()` because the `with self.make_context(...)` block or `try/finally` around normal execution doesn't cover the early-exit branch.
4. **Implement fix**: Ensure `ctx.close()` (which calls all registered `_close_callbacks`) executes in a `finally` block that wraps the entire command invocation, including the case where `SystemExit` is raised due to `ctx.exit()`. This may involve:
   - Wrapping command execution logic in `main()` in a `try/finally`.
   - Or catching `SystemExit`/`Exit` in `invoke()`/`main()`, calling `ctx.close()`, then re-raising.
5. **Verify no double-close**: Make sure context isn't closed twice (e.g., once by normal `with` exit and once by exception handling), which could cause callbacks to run multiple times or errors on already-closed resources.
6. **Run existing tests**: Execute the pre-existing tests (logger fixture test and generic test) to confirm they now pass.
7. **Update documentation**: Add `.. versionchanged::` notes in docstrings for `Context.exit()`, `Context.close()`, or `BaseCommand.main()` explaining the new guaranteed-callback-execution behavior.
8. **Update CHANGES.rst**: Add entry summarizing the fix with link to PR #2680.
9. **Run full test suite**: `pytest` and `tox` to ensure no regressions elsewhere (especially around `CliRunner`, nested contexts, and command groups).
10. **Run pre-commit hooks**: Ensure linting/formatting compliance.

## 3. Risks / Uncertainties

- **Double invocation of callbacks**: If both the normal `with ctx:` exit path and an added `finally`/exception handler call `close()`, callbacks could run twice — need idempotency check or restructure to avoid duplicate close.
- **Nested contexts**: Groups with subcommands create nested `Context` objects; must ensure fix applies correctly at all levels without prematurely closing parent contexts before child command finishes.
- **Exception semantics**: `ctx.exit()` raises `click.exceptions.Exit`, which is caught somewhere and converted to `SystemExit` — need to identify exact exception flow to avoid breaking existing exit-code behavior or swallowing other exceptions.
- **CliRunner interaction**: `CliRunner.invoke()` has its own exception handling and exit code capture logic; changes here must not alter reported `result.exit_code` or `result.output` for existing tests.
- **Backward compatibility**: Some users might rely on callbacks NOT running until process exit (unlikely, but worth confirming no existing tests assume the old behavior).
- **Resource cleanup errors**: If close callbacks raise exceptions themselves during an exit scenario, need consistent handling (should not mask the original exit).
- **Scope of fix**: Determining whether the fix belongs in `Context.exit()`, `BaseCommand.main()`, or both — misplacing it could fix only the `CliRunner` path but not real CLI usage, or vice versa.