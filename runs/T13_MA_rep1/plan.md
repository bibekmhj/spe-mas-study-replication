# Plan: Backport autocompletion fixes for chained commands (#774 → 6.x)

## 1. Files I expect to touch

- `click/_bashcomplete.py` (or equivalent completion module, e.g. `click/_completion.py` depending on 6.x layout) — core logic for resolving completions on chained commands.
- `click/core.py` — possibly, if chained-command resolution/argument parsing needs adjustments that the completion module relies on (e.g. `MultiCommand.resolve_command`, `Group.chain` handling).
- `CHANGES.rst` — add changelog entry noting the backport.
- (No test files will be modified — they already encode expected behavior per task instructions.)

## 2. Steps in order

1. **Locate the original fix**: Review PR #774 on the `master`/newer branch to understand what changed in the bash completion logic for chained commands (likely: correctly walking through multiple subcommands in `ctx`/`args` when `chain=True`, and completing options/arguments for the *last* invoked subcommand rather than the group).
2. **Diff against 6.x**: Compare the current 6.x `_bashcomplete.py` with the fixed version from #774 to identify the equivalent code path (since 6.x may have a different file structure/version of the completion helper than master).
3. **Inspect failing tests**: Run the existing (pre-supplied) test suite related to autocompletion/chained commands to see current failures and pinpoint exact functions exercised (e.g. `get_choices`, `resolve_ctx`, or similar).
4. **Port the fix**:
   - Update the function(s) responsible for walking the command chain (likely `resolve_ctx` or equivalent) to iterate through all matched subcommands when `ctx.command` is a chained `MultiCommand`, rather than stopping at the first.
   - Ensure option/argument completion after a subcommand correctly reflects the *current* (last) subcommand's params, not just the parent group's.
   - Adjust any logic for detecting whether we're still completing a subcommand name vs. an option/argument for an already-resolved subcommand.
5. **Adapt for 6.x differences**: Since this is a backport, account for API/behavior differences between 6.x and master (e.g., older `Context`/`MultiCommand` internals, different helper names) — do not blindly copy code; adapt to the 6.x codebase.
6. **Run the test suite** (without modifying tests) to verify the pre-existing chained-completion tests now pass, and confirm no regressions in non-chained completion tests.
7. **Update CHANGES.rst** with a note referencing the backport and original PR/issue numbers.
8. **Final review**: Re-check diff for minimal, targeted changes consistent with 6.x style/conventions (this is a maintenance branch, so avoid introducing unrelated master-branch features).

## 3. Risks / Uncertainties

- **Version drift**: The 6.x completion module may have diverged enough from master's post-#774 version that a direct patch/cherry-pick won't apply cleanly — may need manual reconstruction of the fix's intent rather than literal porting.
- **Unknown exact root cause**: Without direct access to #774's diff, there's risk of misidentifying which function needs the chain-walking fix (could be `resolve_ctx`, `get_choices`, or argument-parsing helpers).
- **Scope creep**: Chained command support in 6.x might be less mature than master's, so the "same" fix might require additional supporting changes not present in the original PR.
- **Test coupling**: Since tests are pre-written and must not be modified, if my understanding of expected behavior doesn't precisely match the test expectations (e.g., completion ordering, whitespace, exact choice lists), the fix may need iteration to match exact output format.
- **Backward compatibility**: Changes to `MultiCommand`/`Context` resolution logic could inadvertently affect non-completion code paths (e.g., actual command invocation), so changes should be scoped tightly to the completion module where possible.
- **Bash/zsh script differences**: If the fix also touches shipped shell completion scripts, unsure if those exist/need updates in 6.x.