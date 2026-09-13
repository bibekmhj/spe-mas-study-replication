# Plan

## 1. Files I expect to touch

- `click/_bashcomplete.py` (or equivalent completion module, e.g. `click/shell_completion.py` depending on version) — core logic for determining completions
- Possibly `CHANGES.rst` — changelog entry documenting the fix
- No test files should be modified (per instructions), but I will review existing tests (likely `tests/test_bashcomplete.py` or similar) to understand expected behavior

## 2. Steps in order

1. **Reproduce/understand the bug**: Review issue #790 and existing test cases to understand the exact scenario — when a required argument or option is incomplete, subcommands (in a group) or additional chained commands should NOT be offered as completions.
2. **Locate completion logic**: Find the function(s) in `_bashcomplete.py` responsible for:
   - Determining whether the current command has unfulfilled required parameters
   - Deciding whether to recurse into subcommands / offer chained command names
3. **Identify the flaw**: Likely the code checks for incomplete arguments/options but doesn't properly gate the offering of subcommand names when a required param is still pending completion (e.g., completing the value for `--option` or a required positional argument mid-entry).
4. **Add/fix a check**: Introduce logic to detect if the current incomplete word corresponds to completing a required option's value or a required argument, and if so, restrict completions to just that param's choices (or none) — preventing subcommand/chained-command names from being listed.
5. **Verify chained command handling**: Ensure multi-command (`chain=True`) groups also skip offering the next command name when the current command still requires arguments/options.
6. **Run existing tests**: Execute the pre-existing bash completion tests to confirm they pass without modification.
7. **Manual sanity check**: Trace through a couple of scenarios manually (required option expecting a value, required argument not yet given) to confirm subcommands aren't leaking into completion output.
8. **Update CHANGES.rst**: Add a bullet point referencing the fix and issue/PR number.

## 3. Risks / uncertainties

- Uncertain exact Click version/API in this repo snapshot — completion module name and internal function names (`get_choices`, `resolve_ctx`, etc.) may differ; need to inspect actual source before editing.
- Risk of over-restricting completions: fix must only suppress subcommand/chained-command suggestions when a required param is genuinely incomplete, not break normal completion of optional args/options.
- Need to correctly distinguish between "still typing a required option's value" vs "finished with required option, ready for next token" — off-by-one errors in argument parsing state are easy to introduce.
- Chained commands (`chain=True`) may have different code path than plain groups — must handle both without duplicating logic incorrectly.
- Must ensure fix doesn't break completion when all required params are already satisfied (should still offer subcommands normally in that case).
- Existing tests are the source of truth for expected behavior; without modifying them, I need to infer exact expected output format/ordering from their assertions — must not misinterpret them.
- Backward compatibility: changes to shared completion resolution logic could affect other completion tests unrelated to this bug (e.g., plain option/argument completion, custom types with `shell_complete`/`autocompletion` callbacks).