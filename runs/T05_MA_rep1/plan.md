## Plan

**1. Files I expect to touch**
- `src/click/types.py` — likely location of the `Path` parameter type's validation/error-message logic (e.g., `convert()` method where it raises errors for invalid path/file/dir).
- `CHANGES.rst` — add changelog entry documenting the fix.
- Possibly `src/click/exceptions.py` if error formatting/wrapping logic for messages is centralized there rather than per-type.

**2. Steps in order**
1. Reproduce the issue: construct a `click.Path` parameter and pass a value containing `\n` to see the multi-line error output (e.g., using `os.strerror` or a message embedding the raw invalid path).
2. Inspect existing test file(s) already present in the repo describing expected behavior (likely in `tests/test_types.py` or similar) to understand exact expected error string formatting.
3. Locate the code path in `src/click/types.py` where `Path.convert()` raises `self.fail(...)` with messages that may embed the raw path value or OS error string (which can contain newlines, especially on Windows or from `os.strerror`).
4. Modify the error message construction to sanitize/escape newlines — likely by using `repr()` on the offending path segment, or replacing `\n` with a safe representation, so the final message is guaranteed single-line, matching what the pre-existing tests expect.
5. Check other similar error-raising spots (e.g., `File` type, or generic `ParamType.fail`) for the same multiline risk and apply consistent fix if needed.
6. Run the existing test suite, especially the new/pre-existing tests targeting this behavior, to confirm the fix works without modifying test files.
7. Add a `CHANGES.rst` entry referencing issue #2697 and PR #2728.
8. Run full test suite to check no regressions in other Path/File related tests.

**3. Risks / uncertainties**
- Unsure of exact expected format the tests require (e.g., whether newlines should be escaped as `\n` literal text, stripped, or the whole path wrapped in `repr()`) — need to check the pre-existing test file carefully before finalizing message format.
- Risk of breaking existing test snapshots that check exact error message text for `Path` failures (need to verify all current tests still pass with new format).
- Windows vs POSIX path/error string differences (`os.strerror`) could introduce platform-specific newline behavior that's hard to fully replicate/test locally.
- Should confirm whether fix belongs solely in `Path.convert()` or should be generalized in a shared helper (e.g., a `_expand_args`/format utility) to avoid duplicated logic and future regressions in other types.
- Need to ensure fix doesn't affect legitimate multi-line usage messages elsewhere (e.g., custom user-defined multi-line error messages should remain unaffected — only escaping the embedded untrusted path value, not the whole message).