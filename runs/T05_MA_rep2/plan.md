## Plan

**1. Files I expect to touch:**
- `src/click/types.py` — location of `click.Path` parameter type validation logic (where the error message for invalid paths is constructed, e.g. in `convert()`/`fail()` calls).
- `CHANGES.rst` (or equivalent changelog file) — add a note about the fix, if repository convention requires it.

**2. Steps in order:**
1. Locate the `Path` type's error-raising code in `src/click/types.py`, specifically where messages like "... does not exist", "is a file", "is a directory", "is not readable/writable/executable" are constructed, since these typically interpolate the raw path value into the message.
2. Identify the existing test file(s) already present in the tree (likely in `tests/test_types.py` or `tests/test_basic_functionality.py`) that specify the expected single-line behavior when the path contains `\n` (or other newline-like whitespace) — inspect them to understand exact expected format (e.g., whether newlines should be escaped, replaced, or repr'd).
3. Modify the error message construction so that the path value is sanitized before being embedded in the message — e.g., using `repr()` on the path segment, or replacing `\n`/`\r` with escaped representations, so the final message is guaranteed single-line regardless of input.
4. Ensure this sanitization is applied consistently across all error branches in `Path.convert()` (missing, not a file, not a directory, not readable, not writable, not executable, and mismatched cases).
5. Run the existing tests (without modifying them) to confirm the new behavior matches expectations.
6. Update the changelog file with a brief entry referencing the fix and issue number (#2697 / PR #2728), following existing changelog formatting conventions.
7. Do a final review to check no other `ParamType` subclasses (e.g., `File`) have the same multiline issue that might be implicitly covered by the same tests.

**3. Risks / uncertainties:**
- Uncertain exact sanitization approach expected by tests: could be `repr(path)`, `click.utils.escape()`-like helper, or simple `str.replace("\n", " ")` — need to match test expectations precisely without altering test files.
- Risk of breaking existing tests that check exact error message text for normal (non-newline) paths if `repr()` changes quoting/escaping of all paths, not just ones with special characters.
- Need to check whether `os.fspath`/`os.path` representations already interfere with newline paths on different OSes (Windows path separators, etc.), possibly affecting cross-platform test behavior.
- Should verify whether the fix should be localized only to `Path` type or generalized into a shared helper (e.g., in `click.exceptions` or `click.utils`) if other types have similar issues — scope creep risk.
- Changelog file location/format may vary; need to match repo conventions exactly to avoid unrelated diff noise.