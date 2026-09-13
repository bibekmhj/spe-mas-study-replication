## Review Notes

**Does the diff implement the Plan?**
Partially, but via a different (and arguably better) mechanism than the plan anticipated.

- The plan expected the fix to live in `src/click/types.py`'s `Path.convert()`, sanitizing the raw path/error string at the point where `self.fail(...)` is called.
- The actual diff instead fixes the shared `format_filename()` helper in `src/click/utils.py`, adding a translation table that escapes `\n`, `\r`, `\t`, other C0 control chars, and DEL (`0x7F`).
- Since `Path.convert()` (and other types, e.g. `File`) build their error messages using `format_filename()`, this centralizes the fix exactly as anticipated in the plan's risk section ("Should confirm whether fix belongs solely in `Path.convert()` or should be generalized in a shared helper"). This is a reasonable and arguably more robust interpretation of the plan's intent — it addresses the root cause once for all param types that rely on `format_filename`, rather than duplicating logic per-type as step 5 of the plan worried about.

**Missing per the plan**
- **`CHANGES.rst` entry is absent.** The plan explicitly called for a changelog entry referencing issue #2697 / PR #2728 (step 7). This should be added before merging — reviewer should request it.
- No changes to `src/click/exceptions.py` were needed/made — consistent with the plan's "possibly" language, not a problem.
- The plan's step 5 concern ("check other similar error-raising spots... apply consistent fix") is implicitly satisfied by fixing the shared helper, but this isn't explicitly verified/tested for `File` type or other param types that might embed raw paths outside of `format_filename` (e.g., directly interpolating `os.strerror()` text into a message without going through `format_filename`). Worth double-checking there isn't a second unguarded path for OS-level error strings containing embedded newlines (e.g., on some platforms `strerror`-based messages might not pass through this helper).

**Style / implementation observations**
- The `_ESCAPED_TABLE` construction is a bit terse but idiomatic; using `str.translate` is efficient and correct.
- Escaping the full C0 control range (not just `\n`) is more thorough than the plan's narrower framing ("multiline risk") — good defensive choice, but slightly broadens the change's blast radius: any control character embedded in a filename (not just newlines) will now render differently in *all* messages that go through `format_filename`, including non-error/informational output paths, if any exist. Worth confirming `format_filename` is only used for diagnostic/error-style messages and not for any place expecting the literal filename to round-trip (e.g., re-used for further file operations). A quick grep of call sites would be prudent.
- No `repr()`-based approach was taken (one option floated in the plan); instead a custom escape table produces `\n`-style literal text embedded directly in the message (per test: `"my\\ndir" in exc_info.value.message`), consistent with plan's acceptable resolutions ("escaped as `\n` literal text").

**Test coverage**
- New test `test_invalid_path_with_esc_sequence` reproduces the original issue via a real temp directory with an embedded newline and asserts the escaped substring appears in the message. Good, targeted regression test.
- Correctly skipped on Windows since embedded `\n` in path components is not creatable there — sensible platform guard.
- Existing surrogate-related tests (`test_file_surrogates`, `test_file_error_surrogates`) still pass, indicating no regression in the surrogateescape handling path, since translate is applied after decoding.
- Full suite: 38 passed, 1 skipped — no observed regressions.

**Latent regression risk**
- Low risk given test suite passes, but the broadened scope (all control chars, not just newline) is an untested edge case beyond what's asserted (e.g., tab or embedded ESC codes) — the plan's narrower risk statement was about newlines specifically. Not necessarily wrong, but reviewer should confirm this broader escaping is desired/acceptable and won't affect legitimate filenames containing e.g. tabs on unusual filesystems.
- Because the change is in a general-purpose utility (`format_filename`), it could affect any downstream code (including third-party click extensions) that relies on `format_filename` returning the filename unmodified for display purposes — this is a slightly wider surface than the plan's original, narrower scope of "just Path.convert() error messages." Worth flagging as an intentional, disclosed behavior change in the changelog once added.

**Summary**
The diff achieves the plan's core goal (prevent multi-line/control-character injection into error messages) via a more centralized fix than originally planned, which is acceptable and well-tested. However, the **missing `CHANGES.rst` entry** should be added, and it would be good to confirm (via grep or additional tests) that no other message-construction path bypasses `format_filename` and remains vulnerable, and that the broadened escaping of all control characters (not just newlines) doesn't have unintended side effects elsewhere in the codebase.