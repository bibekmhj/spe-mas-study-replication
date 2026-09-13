## Plan

### Files I expect to touch
- `src/click/exceptions.py` — location of `UsageError.show()` (or similar), which currently builds the "Try '... --help' for help." hint using `ctx.help_option_names[0]` (or similar hardcoded/unfiltered lookup) instead of the already-existing `get_help_option_names()` helper that filters out names shadowed by other parameters.
- `CHANGES.rst` — add a changelog entry referencing the fix and issue #2790.
- (Possibly) `src/click/core.py` — only if `get_help_option_names()` itself needs adjustment to be usable from the exception-formatting code path (e.g. if it needs a `Command`/`Context` reference not currently passed through). I expect this file to be untouched, but will check.

I will **not** modify any test files — they already encode the expected behavior.

### Steps
1. Locate the exact hint-generation code (likely `UsageError.show()` or `UsageError.format_message()` in `exceptions.py`) that currently references `ctx.help_option_names` directly.
2. Confirm `Command.get_help_option_names(ctx)` already exists on `core.py` and correctly excludes names claimed by other parameters (per the PR description, this method already exists).
3. Update the hint-building code to call `ctx.command.get_help_option_names(ctx)` (guarding for `ctx` or `ctx.command` being `None`) instead of the raw/unfiltered names list, and use the first entry from the filtered list for the hint text.
4. Handle edge cases:
   - `ctx` may be `None` (hint should be empty as before).
   - The filtered list could be empty if all help option names are shadowed — in that case, no hint should be shown (mirror existing behavior when no help option is defined).
5. Run/inspect the existing (pre-supplied) tests for this issue to confirm expected output strings match (e.g. `"Try 'cli foo --help' for help."`).
6. Add a one-line changelog entry in `CHANGES.rst` under the appropriate unreleased section, referencing issue #2790 and this PR.
7. Run the full test suite (or at least the relevant `tests/test_context.py` / `tests/test_basic.py` / wherever the hint tests live) to ensure no regressions in other hint-related tests (e.g. commands using default `--help` only, or custom help option names via `context_settings`).

### Risks / Uncertainties
- Unsure of the exact current implementation detail in `exceptions.py` (whether it directly indexes `ctx.help_option_names[0]` or computes hint elsewhere, e.g. in `Context.get_usage()`); need to grep for `"Try '"` or `"for help"` string to find all call sites — there may be more than one place needing the same fix (e.g. `NoSuchOption`, `UsageError`, `BadOptionUsage` may each format their own hint, or they may share one code path).
- `get_help_option_names()` signature/behavior needs verification — need to confirm it takes `ctx` and returns a list, and that it's safe to call in contexts where `ctx.command` might not be a `Command` with parameters (e.g. groups vs. commands).
- Need to check if this affects multi-command (`Group`) scenarios differently, since subcommands have their own `Context` with their own parameter list — must ensure the hint uses the correct (sub)command's context, not the parent's.
- Possible i18n/formatting differences (e.g. singular vs plural, quoting style) must match exactly what the pre-existing tests expect.
- Backward compatibility: if any user code relies on `ctx.help_option_names` directly for hints, changing behavior could be a subtle behavior change worth noting in changelog.