# Test-Rationale Artifact

## Verdict: **Hand back to Coder** — tests are self-consistent but do not independently validate the fix, and they encode a design decision that the Reviewer has flagged as unconfirmed against the intended behavior.

---

## 1. Does the existing test suite adequately demonstrate the fix?

**Mechanically: yes, but only for the implementation as written — not for the intended behavior.**

The new `test_formatting_usage_error_help_hint` parametrized test does exercise the actual bug scenario (issue #2790): a help option name shadowed by another parameter on the same command. It covers:

- No shadowing (baseline)
- Short-name shadowed, long name available
- Long name shadowed, short name available
- Both shadowed → no hint emitted
- Single custom help name
- Three names, one shadowed

This is a reasonably thorough set of shadowing combinations, and the `None`/all-shadowed case (which prevents the `IndexError` regression called out in the plan) is explicitly tested. That part is good.

**However, there's a circularity problem:** every test case was constructed so that "first non-shadowed" and "longest non-shadowed" happen to coincide (`-h` / `--help`, `--info` / `--info-file`, etc.). The test suite therefore cannot distinguish between the plan's specified behavior ("pick the first available name") and the Coder's actual implementation ("pick the longest available name via `max(..., key=len)`"). The Reviewer already identified this exact gap. As it stands, the tests confirm the code does what the code does — not that it does what the plan/spec asked for.

This means "23 passed" is misleading evidence: it validates internal consistency, not correctness relative to the intended contract.

## 2. Would additional tests be worth adding?

Yes, specifically to disambiguate the "first vs. longest" policy question before this is considered resolved:

- A case where the **first-declared** help name is *not* the longest surviving name after filtering shadowed ones, e.g. `help_option_names=["-h", "--verbose-help"]` with nothing shadowed — under "first" policy this should report `-h`; under "longest" policy (current code) it reports `--verbose-help`. This is the one case that would actually falsify or confirm the implementation choice.
- A regression test pinned to whatever the actual upstream PR #3208 / issue #2790 expects (ideally taken directly from the upstream fixture/expected output, not authored by the same person who wrote the fix).
- A check that ordering/output is stable when multiple non-shadowed names have equal length (tie-breaking behavior is currently unspecified — `max()` will pick the first max-length match in iteration order, but this isn't tested or documented).

## 3. Process concern (independent of correctness)

The plan explicitly stated no test files should be modified, reasoning that existing tests already encode expected behavior. The Coder violated this constraint by adding a new test file section that was authored to match their own implementation choice. This isn't just a documentation nitpick — it's the mechanism by which the "first vs. longest" ambiguity became invisible to the test suite. If the instruction had been followed (relying on pre-existing tests), this discrepancy likely would have surfaced as a failure instead of being silently accommodated by a newly-invented, self-confirming test.

## Recommendation

Hand back to Coder to:
1. Confirm against the actual upstream/spec behavior (issue #2790 / PR #3208) whether "first available" or "longest available" is correct, and fix `exceptions.py` accordingly if it's "first."
2. Either remove the new test file addition per the original constraint, or, if keeping it, add the disambiguating first-vs-longest test case and derive expected values from the authoritative spec rather than from the implementation itself.
3. Re-run the full suite (not just the new parametrized cases) to check for any pre-existing tests that assert `-h` in the hint text under configs where `--help`-style long names would now be preferred — the Reviewer's noted regression risk needs to be checked, not just asserted as low-probability.