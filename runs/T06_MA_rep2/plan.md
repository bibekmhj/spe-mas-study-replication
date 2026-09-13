## Plan

### 1. Files expected to touch
- `src/click/core.py` — main location of `Option`/`Parameter` default-resolution logic (where `UNSET` sentinel is normalized to `None`), likely in `Option.__init__`, `get_default`, or wherever multiple option declarations sharing a name are merged/processed.
- `CHANGES.rst` — add a changelog entry once the correct section/header is confirmed (may need to add a new "Unreleased" header if none exists).
- Possibly `src/click/types.py` or wherever the `UNSET` sentinel is defined, if normalization happens in a shared helper.

Test files are already present and should NOT be modified — only used to verify the fix.

### 2. Steps in order

1. **Reproduce the bug**: Run the existing new test (pointing two flags at the same parameter declaration, one with a default and one without) to confirm it currently fails, and understand the exact failure mode (order-sensitivity of default resolution).
2. **Locate UNSET normalization logic**: Search `core.py` for where `UNSET` (the sentinel for "no default given") is converted to `None`. This is likely during `Option`/`Parameter` construction or during declaration merging when multiple flags share a destination.
3. **Understand current flow**: Identify why normalization currently happens too early — likely during per-flag processing, before all flags contributing to the same parameter have been examined, causing the *first-seen* flag's UNSET to eagerly become `None` and overwrite a later flag's real default.
4. **Redesign default resolution**: Change logic so that:
   - Each flag's default is initially kept as `UNSET` (not normalized) during per-declaration processing.
   - After all flag declarations for a parameter are collected/merged, resolve the final default value by picking the first non-UNSET value among them.
   - Only at that final point, if all values are still `UNSET`, normalize to `None`.
5. **Ensure no regressions in default handling elsewhere**: Check other places relying on `UNSET` vs `None` distinction (e.g., `show_default`, `required` inference, `prompt` defaults, type coercion) to make sure deferring normalization doesn't break assumptions that default is already `None`-normalized by the time those code paths run.
6. **Run the new test** (already present) to confirm it now passes, and run the full test suite to check for regressions, especially around option defaults, flag value parsing, and multiple-declaration options.
7. **Add changelog entry**: Check `CHANGES.rst` for existing "Unreleased"/"Version X.Y.Z (unreleased)" header; if missing, add one following project conventions, then add a concise entry describing the fix (referencing issue #3071 and PR #3079).
8. **Final review**: Double check that `UNSET` sentinel is still exported/used consistently elsewhere, and that public API behavior (e.g., `param.default` attribute value seen by users) remains `None` post-parsing as before, only the *internal* resolution order changed.

### 3. Risks / uncertainties

- **Ambiguity in exact code location**: Without seeing the current `core.py` implementation, it's unclear whether `UNSET` normalization happens in `Option.__init__`, `Parameter.__init__`, a shared `_parse_decls` method, or in `Command.parse_args`/`process_value`. Need to search codebase carefully to find all normalization points to avoid missing one.
- **Multiple normalization sites**: There may be more than one place that converts `UNSET` to `None` (e.g., once at construction, once at value resolution) — need to ensure all are deferred consistently, not just one.
- **Behavior for flags/is_flag options**: Flags often have implicit defaults (`False`/`True`); need to ensure the change doesn't affect flag-specific default logic, only genuinely shared/aliased parameter declarations.
- **Backward compatibility**: Some user code or internal tests might rely on `default` being `None` immediately after parameter construction (before parsing) rather than `UNSET`; must confirm no public-facing attribute changes in an unexpected way.
- **Changelog header placement**: Uncertain whether to add a new "Unreleased" version header or append to an existing latest release section — may need to check repository conventions/git history or ask for guidance, as the PR description itself notes this uncertainty.
- **Test isolation**: Since test files already exist and must not be modified, need to ensure the fix's implementation aligns exactly with what those tests expect (e.g., exact attribute names, error messages, ordering semantics) — mismatches would require re-reading test expectations carefully rather than adjusting tests.
- **Edge cases with multiple UNSET defaults**: Need to verify behavior when *all* flags for a parameter are UNSET (should still normalize to `None`), and when *multiple* flags have explicit non-UNSET defaults (which one wins — likely first declared, per PR description "first non-UNSET default value").