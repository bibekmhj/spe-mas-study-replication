# Plan: Fix Usage Wrapping on Narrow Terminals (Issue #231 / PR #240)

## 1. Files I Expect to Touch

- `click/formatting.py` — likely home of `HelpFormatter`, `wrap_text`, and text-wrapping logic used to build usage strings.
- `click/core.py` — possibly where `format_usage`/`Command.get_usage` composes the "Usage: prog cmd [OPTIONS]..." line and calls into wrapping helpers.
- Test files already present (do NOT modify) — will use them to identify expected behavior, likely `tests/test_formatting.py` or `tests/test_basic.py` containing narrow-terminal usage wrapping assertions.
- Possibly `click/_compat.py` if terminal width detection is involved (unlikely to need changes, but worth checking).

## 2. Steps in Order

1. **Reproduce the bug**: Run existing tests related to usage wrapping to see current failures, and manually construct a case with long prog name/options on a narrow terminal width to observe incorrect wrapping.
2. **Locate wrapping logic**: Find where `textwrap.TextWrapper` (or a subclass) is used to wrap the "Usage:" line, especially where `subsequent_indent` is set — this is the flagged problem area per PR description.
3. **Understand the root cause**: Confirm that `TextWrapper` counts `subsequent_indent` length as part of the wrap width, causing incorrect wrapping when the indent (aligned under "Usage: ") plus content exceeds narrow terminal width, or causing under-wrapping/over-wrapping.
4. **Design a fix**: Rather than rewriting `TextWrapper`, apply a workaround such as:
   - Adjusting the target `width` parameter passed to `TextWrapper` to account for the indent length (e.g., subtracting indent length from width before wrapping, or padding differently).
   - Or post-processing wrapped lines to correct indentation without exceeding terminal width.
5. **Implement the fix** in the identified wrapping function/class (likely a custom `HelpFormatter.write_usage` or a `wrap_text` helper in `formatting.py`).
6. **Run the pre-existing tests** describing expected wrapping behavior to validate the fix without modifying those test files.
7. **Check for regressions**: Run the full test suite to ensure normal (wide terminal) usage formatting and other help text wrapping (options, epilog, etc.) still behave correctly.
8. **Manually verify edge cases**: very narrow widths, very long program names, multiple options, subcommands — ensure no crashes (e.g., negative width) and reasonable output.
9. **Clean up**: add comments explaining the workaround and why `subsequent_indent` width inclusion is problematic, referencing the upstream issue.

## 3. Risks / Uncertainties

- **Not a full fix**: As noted by the PR author, this is a workaround, not a proper fix of `TextWrapper`'s behavior — there may be edge cases (extremely narrow widths, unicode/wide chars) that remain broken.
- **Negative or zero width**: Adjusting width by subtracting indent length risks producing a non-positive width for `TextWrapper` on very narrow terminals, which could raise exceptions — need bounds checking.
- **Scope creep**: Changes to shared wrapping utilities might affect other help text sections (option descriptions, epilogs) beyond just the usage line — need to scope the fix narrowly if possible, or verify all callers.
- **Test coverage ambiguity**: Since test files are pre-existing and not to be modified, need to infer exact expected output format (spacing, line breaks) precisely from them; mismatched assumptions could make the fix seem correct while still failing tests.
- **Terminal width detection differences**: Behavior might differ across environments if width is inferred from `COLUMNS` env var or actual terminal size in CI vs. local testing — tests likely mock/set width explicitly, but worth confirming.
- **Backward compatibility**: Any width/indent calculation change might subtly alter output for already-passing wide-terminal cases; must verify no unintended formatting changes elsewhere.