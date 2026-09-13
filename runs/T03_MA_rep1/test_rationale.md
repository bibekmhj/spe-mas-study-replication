## Test-Rationale Artifact

**Verdict: Adequate, but with a gap worth flagging back to the Coder/team before calling this fully closed.**

### What the new test demonstrates well

`test_custom_command_no_parens` is a well-targeted regression test:

- It exercises the exact failure mode described (a `Group` subclass with a custom `command_class`, invoking `@grp.command` bare — no parens, no kwargs).
- It asserts `result.exception is None`, which directly guards against the `TypeError`/assertion failure that the reordering fixes (previously, `kwargs["cls"]` being pre-populated broke the `not args and not kwargs` bare-decorator detection in `command()`).
- It confirms the command actually runs and produces output, not just that no exception was raised — a stronger check than merely inspecting `cli.__class__`.
- It sits right next to the pre-existing `test_command_no_parens`, so it clearly reads as "same scenario, but with a custom command class," which aids future maintainers.

Test output (`4 passed`) confirms it exercises the changed code path successfully alongside the other 3 existing decorator tests, and presumably fails without the fix (reordering `kwargs["cls"]` injection after the bare-func detection) — though this wasn't explicitly verified in the artifacts given (no "before fix" red run shown).

### Gaps / concerns

1. **Missing type assertion.** The test never asserts `isinstance(cli, CustomCommand)` or `type(cli) is CustomCommand`. The whole point of `command_class` is that the decorator should tag the command with the custom class. The test only proves the bare-decorator path doesn't crash and runs correctly — it does **not** prove that `cls=CustomCommand` was actually threaded through. A regression that silently dropped the `cls` injection entirely (defeating the purpose of `command_class`) would still pass this test. This is the most important omission.

2. **No parenthesized-call coverage with `command_class`.** The plan/bug was specifically about the *no-parens* bare-decorator path, but there's no companion test confirming `@grp.command()` (with parens) still correctly picks up `command_class` too — i.e., that the reordering didn't break the non-bare case. Given the fix moves code across a branch boundary, testing both branches (bare and called-with-args) is warranted.

3. **No test for explicit `cls` override.** Should verify that if a caller explicitly passes `cls=SomethingElse` to `@grp.command(cls=Other)`, the explicit value wins over `command_class` — this exercises the `kwargs.get("cls") is None` guard, which is adjacent to the moved code and easy to accidentally break in a future refactor.

4. **Reviewer's note about plan/diff location mismatch is a documentation issue, not a test issue** — but it does suggest the "why" of the fix wasn't fully validated against the original hypothesis. If the plan assumed the bug was in `decorators.py`, it's worth double-checking there isn't a *second*, related bug lurking there that this diff doesn't address (e.g., calling `command_class`-based groups through other entry points like `add_command` combined with parametrized decorators, or `Group.group()`'s analogous logic if it has similar kwargs-ordering issues).

### Recommendation

**Do not block the fix** — the core regression (crash on bare `@grp.command` with a custom `command_class`) is correctly reproduced and fixed, and the diff itself is minimal and low-risk (pure reordering, no logic change).

However, **send back a follow-up test request to the Coder** (not necessarily a code fix) to:
- Add `assert isinstance(cli, CustomCommand)` to the existing test.
- Add a sibling test for `@grp.command()` (with parens) + `command_class`.
- Optionally add a test for explicit `cls=` override beating `command_class`.

These are low-cost additions that would close the verification gap and guard against silent regressions in the `cls`-injection logic itself, not just the crash symptom.