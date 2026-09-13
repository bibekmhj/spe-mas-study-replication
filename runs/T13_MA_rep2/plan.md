# Plan: Backport autocompletion fixes for chained commands (#774 → 6.x)

## 1. Files I expect to touch

- `click/_bashcomplete.py` — core autocompletion logic; likely location of the chained-command traversal/completion bug.
- `click/core.py` — possibly needs minor changes if the completion logic relies on `MultiCommand`/`Group.chain` attributes or command resolution helpers that differ between master and 6.x.
- `CHANGES.rst` (or `CHANGES`) — add changelog entry noting the backport, matching project convention.
- Possibly `click/types.py` if completion for parameter types (e.g., `Choice`) is involved in the original fix.

(Test files already present are off-limits; only production code + changelog should change.)

## 2. Steps in order

1. **Locate and read original PR #774** (or its diff/commit) to understand exactly what changed on master — likely fixes to `get_choices`/`resolve_ctx` logic in `_bashcomplete.py` to properly walk chained subcommands and their parameters when completing.
2. **Inspect existing 6.x `_bashcomplete.py`** to find the equivalent code path and confirm whether the file structure differs enough to require adapting the patch rather than a straight cherry-pick.
3. **Run the existing test suite (bash completion tests)** first to see current failures — identify which tests (already present) are failing without the fix, confirming the bug reproduction.
4. **Apply the fix**: adjust the context-resolution function that walks parsed args across chained (multi-)commands so that:
   - It correctly continues into subcommand contexts for `chain=True` groups.
   - Completions consider parent group options/params as well as the current subcommand's params.
   - Handles the case where multiple chained commands appear before the cursor position.
5. **Verify no regressions** for non-chained (single) command groups — ensure normal completion still works.
6. **Update CHANGES.rst** with a note referencing the backport and original issue/PR numbers.
7. **Re-run full test suite**, focusing on `tests/test_bashcomplete.py` (or equivalent), to confirm all previously failing tests now pass and nothing else breaks.
8. **Review diff for minimal, targeted changes** consistent with 6.x style (this is a maintenance branch — avoid introducing unrelated master-only refactors).

## 3. Risks / Uncertainties

- **API drift between master and 6.x**: `_bashcomplete.py` may have diverged (e.g., different internal function signatures like `resolve_ctx`, `get_user_autocompletions`), so the patch may not apply cleanly and needs manual adaptation.
- **Behavior of `Group(chain=True)` context building**: risk of subtly breaking completion for non-chained groups if the shared code path is modified incorrectly.
- **Test coverage assumptions**: since test files are pre-existing and must not be modified, I need to ensure my fix exactly matches the expected behavior encoded in those tests, not just the master fix's intent — there could be minor semantic differences in 6.x's completion API.
- **Optional args / eager params**: chained command completion often has edge cases with optional trailing arguments and eager parameters (e.g., `--help`); need to ensure these still short-circuit correctly.
- **Windows/argument-splitting quirks**: bash completion tests sometimes have environment-specific behavior; must ensure changes don't depend on features only in master's newer parsing code.
- **Changelog placement**: uncertain exact format/location expected in 6.x `CHANGES.rst` (unreleased section vs. new version heading).