## Review Notes

**Does the diff implement the Plan?**
Partially, but via a different (and arguably better) location than the plan anticipated.

- The plan explicitly targeted `src/click/types.py`'s `Path.convert()` error-message construction. The actual diff instead patches `format_filename()` in `src/click/utils.py`, escaping `\n`→`\\n` and `\r`→`\\r`.
- This works because `Path.convert()` (and likely `File`) delegate filename formatting to `format_filename()`, so the fix is applied at a shared choke point rather than being duplicated across every error branch (missing/not-a-file/not-a-directory/not-readable/etc.). This actually satisfies **Step 4** ("consistent across all error branches") more robustly than patching each `fail()` call individually, and also addresses **Step 7**'s concern about `File` and other `ParamType` subclasses sharing the same issue, since they likely reuse `format_filename()` too.
- **Step 6 (changelog update) is not fulfilled** — no `CHANGES.rst` entry was added referencing #2697/#2728. This should be flagged as a gap versus repo convention, even though it doesn't affect test correctness.
- Step 2 ("inspect existing tests to understand expected format") appears honored: the new test asserts `"my\\ndir"` in the message, matching a simple escape-replace strategy rather than `repr()`, avoiding the quoting/escaping risk called out in the Risks section.

**Style / Correctness observations:**
- The sanitization (`str.replace("\n", "\\n").replace("\r", "\\r")`) is simple, readable, and low-risk compared to `repr()`, correctly avoiding the anticipated regression risk of altering quoting for all paths.
- The new test (`test_invalid_path_with_esc_sequence`) only covers the "missing file" branch (`dir_okay=False` on a directory that doesn't behave as a file). It does not directly test other branches (not readable/writable/executable, wrong type), but since the fix lives in the shared `format_filename()`, this is acceptable — just worth noting as a coverage gap in the review, not a bug.
- Test correctly skips on Windows due to path syntax differences — reasonable and consistent with existing patterns in the test file (see `test_file_surrogates`).

**Latent regressions / risks:**
- `format_filename()` is used elsewhere in the codebase (e.g., in messages beyond `Path`/`File` param types, possibly in `echo`-related helpers or other error formatting). Since this change alters its output for **any** filename containing `\n`/`\r`, double-check no other test or downstream consumer relies on raw (unescaped) newline-containing filenames being passed through verbatim. The full suite passing (38 passed, 1 skipped) is reassuring but doesn't guarantee no behavioral change for non-tested call sites (e.g., real-world filenames with `\r` in echoed messages).
- No changelog entry — should be added for completeness per plan Step 6 and typical repo hygiene.
- The fix's scope (global to `format_filename`) is broader than the plan scoped ("localized only to `Path` type" was flagged as an open question) — this should be called out explicitly as an intentional generalization, and confirmed as desired rather than accidental scope creep.

**Verdict:** The diff achieves the functional goal of the plan (single-line error messages for paths containing newlines) via a cleaner, more centralized fix than originally planned, and tests pass. However, it deviates from the planned file location, omits the changelog update, and provides only partial direct test coverage of the various `Path.convert()` failure branches (though likely covered transitively). Recommend adding a `CHANGES.rst` entry before merging, and optionally verifying no other test/module depends on unescaped filenames from `format_filename()`.