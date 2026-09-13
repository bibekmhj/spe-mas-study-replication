## Plan

### 1. Files to touch
- `src/click/core.py` — primary location where option defaults are resolved/normalized (likely in `Option.get_default`, `Parameter.get_default`, or wherever `UNSET` is converted to `None`, and in the multi-option/param declaration merging logic that combines multiple flag definitions sharing a target parameter).
- `CHANGES.rst` — add a changelog entry once the correct section/header convention is confirmed (add a new "Unreleased" section if none exists, following repo convention).
- (Possibly) `src/click/types.py` or wherever `UNSET` sentinel is defined, if normalization logic lives there rather than in `core.py`.
- Do NOT touch test files (already present per instructions).

### 2. Steps in order
1. Locate the `UNSET` sentinel definition and all places it's referenced in `core.py` (search for `UNSET`) to understand current normalization points.
2. Identify where multiple option declarations (e.g., two flags mapped to the same `dest`/parameter name) get merged and where defaults are computed — likely in `Command.parse_args` or `Option.process_value` / `Option.full_process_value` / `Option.resolve_envvar_value` or in the parser's handling of grouped options.
3. Trace the current flow: find where `UNSET -> None` conversion currently happens (probably too early, before all flags contributing to the same parameter have been evaluated), causing order-sensitivity when one flag has an explicit default and another has `UNSET`.
4. Modify the logic so that:
   - Each flag's default is evaluated but kept as `UNSET` if not explicitly set, rather than immediately converting to `None`.
   - After all flags/options contributing to a parameter have been processed, pick the first non-`UNSET` default value (if any); only fall back to `None` normalization at the very end, once no explicit default was found across all contributing declarations.
5. Ensure this deferred normalization doesn't break other flows (e.g., single-option case, flag pairs like `--flag/--no-flag`, envvar resolution, `is_flag` boolean defaults, `multiple`/`count` params).
6. Run the existing test (already present in the working tree) that pins two flags to the same param declaration with only one default, confirming order-independence.
7. Run full test suite for `core.py` / options to check no regressions (default handling, flag defaults, boolean flags, count/multiple params, prompt defaults, etc.).
8. Update `CHANGES.rst`:
   - Check if there's an "Unreleased"/"Version X.Y.Z (unreleased)" header; if not, add one following existing style used in prior releases.
   - Add a concise entry describing the fix and referencing the issue/PR number.
9. Review diff for minimal, targeted changes confined to default-resolution logic.

### 3. Risks / uncertainties
- Uncertain exact location(s) where `UNSET -> None` conversion currently occurs; may be spread across multiple methods (`get_default`, `process_value`, `handle_parse_result`), risking incomplete fix if only one site is patched.
- Risk of breaking other default-resolution paths that rely on immediate `None` normalization (e.g., type casting, callback processing, `show_default` logic, `required` checks) if the sentinel now persists longer than before.
- Interaction with `multiple=True` or `count` options, and with `flag_value` options, could have edge cases not covered by the new test.
- Need to confirm whether `UNSET` is a click-level sentinel or new addition tied to this PR itself — if newly introduced, must ensure it's defined consistently and exported/used wherever needed.
- Changelog placement is ambiguous per the issue text itself — must infer correct convention from repo history (last version header format) without an explicit maintainer answer.
- Must avoid regressing behavior for the common single-flag-per-parameter case, which should remain unchanged in output.
- Backward compatibility: any external code inspecting default value expecting immediate `None` at an earlier stage (e.g., via callbacks invoked mid-parsing) could observe `UNSET` instead of `None` if normalization is deferred too far — need to double check all consumption points of a parameter's default before final resolution.