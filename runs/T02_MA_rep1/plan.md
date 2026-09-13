## Plan

**1. Files I expect to touch**
- `src/click/core.py` — most likely location of the argument/option synopsis or usage-string generation logic (e.g., `make_metavar`, `get_usage_pieces`, or similar methods on `Argument`/`Parameter` classes that wrap metavars in brackets for optional parameters).
- Possibly `src/click/types.py` — if the `Choice` type itself contributes bracket formatting to the metavar string (e.g., `get_metavar` on `Choice`).
- No test files will be modified (per instructions), but I will inspect them to understand expected output format.

**2. Steps in order**
1. Locate the referenced prior fix PR #3507 (commands version) to understand the pattern of the bug and its fix — search for similar bracket-wrapping logic already patched for commands, to replicate the approach for arguments/options.
2. Search codebase for where metavars are wrapped in `[...]` for optional parameters — likely in `Parameter.make_metavar()` or `Argument.make_metavar()` in `core.py`.
3. Search for where `Choice.get_metavar()` (in `types.py`) builds the choice list string — check if it already adds brackets (e.g., `[a|b|c]`) itself.
4. Identify the double-bracketing: likely the metavar building code wraps the already-bracketed choice string in another set of brackets when the argument/option is optional (not required), producing `[[a|b|c]]`.
5. Locate and inspect the relevant test file(s) already present (e.g., in `tests/test_arguments.py` or `tests/test_basic.py` related to synopsis/usage) to confirm exact expected output strings.
6. Fix the logic so brackets are only applied once — either by not re-wrapping when the metavar already contains brackets, or by centralizing bracket-wrapping so `Choice.get_metavar()` doesn't add its own brackets and instead relies on the parameter-level wrapping (mirroring the fix used for commands in #3507).
7. Run the existing test suite (particularly the pre-existing tests for this issue) to confirm the fix resolves the double-bracket issue without breaking other usage/help output tests.
8. Check for other parameter types or places (e.g., `nargs` variadic arguments, multiple choice combined with optional flags) where similar double-wrapping could occur, to ensure fix is complete and consistent.

**3. Risks / things I'm unsure about**
- The exact mechanism causing double brackets — need to confirm whether the issue is in `Parameter.make_metavar()`, `Argument.make_metavar()`, or `Choice.get_metavar()` before editing.
- Fixing bracket logic in one place might not cover all cases (e.g., required vs. optional arguments/options, `nargs > 1`, `multiple=True`) — must verify against all pre-existing test cases.
- The mirrored fix from #3507 (for commands) may use a different internal structure than arguments/options, so the pattern may need adaptation rather than direct copy.
- Risk of breaking other formatting tests that rely on current bracket behavior for non-Choice types (e.g., plain optional arguments with single brackets) — need to ensure backward compatibility for those cases.
- Need to check help text (`get_help_record`) generation too, since brackets may appear there separately from the usage synopsis, and the fix should be scoped only to the usage synopsis if that's what the issue concerns (avoid unintended scope creep).