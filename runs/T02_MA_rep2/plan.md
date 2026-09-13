## Plan

**1. Files I expect to touch:**
- `src/click/core.py` — likely location of `Argument`/`Option` (or `Parameter`) synopsis/usage-piece generation logic (e.g., `make_metavar`, `get_usage_pieces`, or similar method that wraps metavar/choices in brackets for optional arguments).
- Possibly `src/click/types.py` — if `Choice` type itself contributes bracket formatting to the metavar string (e.g., `Choice.get_metavar`).
- No test files should be modified (per instructions), but I will inspect existing tests (likely in `tests/test_arguments.py` or `tests/test_basic_commands.py`) to understand expected output format.

**2. Steps in order:**
1. Reproduce the issue: search codebase for where usage/synopsis strings are constructed, focusing on `Argument.make_metavar()`/`Parameter.make_metavar()` and any code that wraps metavar in `[...]` when `required=False`.
2. Locate the double-bracketing: identify two places that both add brackets — e.g., `Choice.get_metavar()` may already return `[choice1|choice2]`, and then the argument/option synopsis code wraps it again in `[...]` because the parameter is optional, producing `[[choice1|choice2]]`.
3. Compare with the analogous fix from PR #3507 (commands) to understand the pattern used there — likely they stopped double-wrapping by checking if the metavar already contains brackets, or restructured so bracket-wrapping for optionality happens only once, independent of `Choice`'s own bracket formatting.
4. Apply the equivalent fix for arguments: modify the metavar-building method so that:
   - `Choice.get_metavar()` continues to produce `[choice1|choice2]` (its own bracket notation for choices).
   - The optional-argument wrapping logic (adding brackets for non-required args) does not add an additional layer of brackets when the metavar already represents a choice set enclosed in brackets — instead reusing the same approach as the command-level fix (e.g., checking a flag or restructuring string formatting to avoid nesting).
5. Run the existing test suite (`tests/test_arguments.py`, `tests/test_options.py`, and any synopsis/usage-related tests) to confirm expected single-bracket output now passes without modifying test files.
6. Run full test suite to check no regressions in other usage-string formatting (options, multiple choices, flag values, etc.).
7. Review CHANGES.rst / add changelog entry if project convention requires it (check if PR #3507 added one, mirror that).

**3. Risks / uncertainties:**
- Uncertain exact internal structure of `Choice.get_metavar()` vs `Parameter.make_metavar()` — need to read current source to see how bracket wrapping happens for both required and optional params, and for both `Argument` and `Option` types (issue may apply to only one).
- The fix for commands (#3507) may use a different mechanism (e.g., dealing with subcommand listing) than what's needed for choices in arguments — mapping the analogous fix isn't guaranteed to directly transfer; may need a distinct approach.
- Multiple value arguments (`nargs=-1` or `nargs>1`) combined with `Choice` might have separate bracket logic that also needs fixing, increasing scope.
- Must ensure fix doesn't break cases where brackets are intentionally doubled (e.g., truly optional list of choices where nested brackets might be semantically correct, e.g. `[[a|b]]` meaning optional choice — need to verify against test expectations already in the repo).
- Changelog/version file conventions unknown without inspecting repo state.