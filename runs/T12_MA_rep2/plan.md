## Plan

**1. Files I expect to touch:**
- `click/formatting.py` (or wherever `HelpFormatter`/`wrap_text` and usage-writing logic lives) — core fix location for text wrapping behavior.
- `click/utils.py` (possibly, if wrapping helpers live there instead)
- Possibly `click/core.py` — if `format_usage`/`Command.format_usage` builds the string that gets wrapped and needs adjustment in how prefix/indent is passed.
- No test files will be modified (per instructions), but I will inspect them to understand expected wrapped output.

**2. Steps in order:**
1. Locate and re-read issue #231 context and the existing tests related to usage wrapping (likely in `tests/test_formatting.py` or `tests/test_basic.py`) to understand exact expected output for narrow terminal widths.
2. Reproduce the bug: construct a command with a long usage line (many params) and format it with a narrow terminal width to see the current (incorrect) wrapping output.
3. Identify the root cause: `TextWrapper` from `textwrap` module accounts for `subsequent_indent` length when computing available width for the *first* line/segment, causing incorrect wrap points when `initial_indent` differs from `subsequent_indent` (typical usage-prefix case, e.g. `Usage: prog ` vs continuation indent).
4. Inspect the current implementation of the wrapping helper (likely a custom subclass of `textwrap.TextWrapper` or a call site in `HelpFormatter.write_usage`) to see how indents/width are being computed.
5. Implement a fix: adjust how the wrapper computes width/indent so that the subsequent_indent's length isn't incorrectly factored into wrapping decisions for the initial line — likely by:
   - Passing consistent width regardless of indent lengths, or
   - Overriding `_wrap_chunks` / using a custom subclass that computes wrapping based on max(initial, subsequent) indent lengths correctly, or
   - Manually handling the usage line wrapping (splitting prefix and args) instead of relying purely on `textwrap.TextWrapper` defaults.
6. Run the existing test suite (particularly the pre-existing tests describing expected wrapped usage behavior) to verify the fix produces correct output without modifying those test files.
7. Manually verify with a few edge cases: very narrow width, single long argument name, multiple options, to ensure no regression in normal (wide terminal) wrapping.
8. Clean up: ensure no leftover debug code, and that the fix is minimal and scoped to the wrapping logic.

**3. Risks / uncertainties:**
- The original PR author explicitly states discomfort with the fix, implying it's a workaround rather than a full solution — risk of not fully matching upstream's actual accepted fix, especially if there were follow-up PRs refining this further.
- `textwrap.TextWrapper` internals vary slightly across Python versions; a fix that patches around indent-width computation could behave differently depending on the Python version running the tests.
- Risk of the fix being too narrow (only handling the specific usage-prefix case) and not generalizing to other multi-indent wrapping call sites in the codebase (e.g., option help text wrapping).
- Need to be careful not to break existing wide-terminal wrapping tests while fixing the narrow-terminal case — regression risk on already-passing behavior.
- Uncertain exactly which module/function contains the wrapping logic without direct repo access; may need to search for `TextWrapper`, `wrap_text`, or `format_usage` to pinpoint exact call site.
- Terminal width edge cases (width smaller than the indent itself) could cause negative wrap widths — need defensive handling if not already present.