"""Enumerate candidate bug-fix tasks for the study task set.

PR-first selection: enumerate merged PRs directly, filter for bug-fix titles
and small-diff shape, apply the exclusion filters. The PR is the ground truth
for the fix (a concrete diff plus tests). Linked issues are captured when
available but are not required.

This replaces the earlier issue-first approach, which was blocked by
inconsistent issue-to-PR linking in the target repository.
"""
import json
import os
import re
import time
from pathlib import Path

from github import Github, Auth, RateLimitExceededException, GithubException

REPO = "prompt-toolkit/python-prompt-toolkit"
CUTOFF_DATE = "2027-01-01"
BUG_TITLE_PATTERNS = [
    r"\bfix(?:e[sd])?\b",
    r"\bbug\b",
    r"\bresolv(?:e|es|ed)\b",
    r"\bcorrect(?:s|ed)?\b",
    r"\brepair\b",
    r"\bpatch(?:es|ed)?\b",
    r"\bissue\b",
    r"\bregression\b",
    r"\bbroken\b",
    r"\bcrash\b",
    r"\berror\b",
    r"\bfail(?:s|ed|ure)?\b",
]
EXCLUDED_PATH_PATTERNS = [
    r"^prompt_toolkit/renderer\.py",
    r"^prompt_toolkit/layout/",
    r"^prompt_toolkit/key_binding/",
    r"^docs/",
    r"^examples/",
    r"^tests/",
    r"^CHANGELOG",
    r"^README",
    r"\.md$",
    r"\.rst$",
]
MAX_LOC = 300
MAX_FILES = 4
MIN_LOC = 3   # excludes trivial one-line PRs which are often typo fixes
ISSUE_REF_PATTERN = re.compile(
    r"(?:^|\s|[(\[,.])(?:GH-|gh-|#)(\d{1,6})\b"
)
BUG_TITLE_RE = re.compile("|".join(BUG_TITLE_PATTERNS), re.IGNORECASE)


def is_excluded_path(path):
    return any(re.search(p, path) for p in EXCLUDED_PATH_PATTERNS)


def is_bug_fix_title(title):
    return bool(BUG_TITLE_RE.search(title or ""))


def safe_call(fn, retries=3):
    for attempt in range(retries):
        try:
            return fn()
        except RateLimitExceededException:
            time.sleep(60)
        except GithubException as e:
            if e.status in (403, 502, 503):
                time.sleep(30 * (attempt + 1))
            else:
                raise
    return None


def collect_issue_refs(text):
    if not text:
        return set()
    return {int(m) for m in ISSUE_REF_PATTERN.findall(text)}


def show_rate_limit(gh):
    try:
        rl = gh.get_rate_limit()
        core = getattr(rl, "core", None) or getattr(rl.resources, "core", None)
        return core.remaining
    except Exception:
        return "unknown"


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN before running.")
    gh = Github(auth=Auth.Token(token))
    repo = gh.get_repo(REPO)

    print("Enumerating all closed PRs (this is the slow phase)...")
    pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

    candidates = []
    rej = {"not_merged": 0, "not_bug_title": 0, "too_many_files": 0,
           "too_much_loc": 0, "too_little_loc": 0,
           "excluded_path": 0, "no_code_files": 0, "error": 0}
    seen = 0

    for pr in pulls:
        seen += 1
        if seen % 50 == 0:
            print(f"  scanned {seen} PRs, candidates so far: {len(candidates)}, "
                  f"API calls remaining: {show_rate_limit(gh)}")

        if not pr.merged:
            rej["not_merged"] += 1
            continue
        if not is_bug_fix_title(pr.title):
            rej["not_bug_title"] += 1
            continue

        try:
            files = safe_call(lambda: list(pr.get_files()))
        except Exception:
            rej["error"] += 1
            continue
        if files is None:
            rej["error"] += 1
            continue

        file_paths = [f.filename for f in files]
        loc = sum(f.additions + f.deletions for f in files)

        # Exclude PRs whose diff is entirely docs/tests/examples/config
        code_files = [p for p in file_paths if not is_excluded_path(p)]
        if not code_files:
            rej["no_code_files"] += 1
            continue
        # If any file is in the excluded-implementation paths, skip
        # (rendering/layout/key-binding code, per §3.3)
        if any(re.match(EXCLUDED_PATH_PATTERNS[0], p) or
               re.match(EXCLUDED_PATH_PATTERNS[1], p) or
               re.match(EXCLUDED_PATH_PATTERNS[2], p)
               for p in file_paths):
            rej["excluded_path"] += 1
            continue

        if len(file_paths) > MAX_FILES:
            rej["too_many_files"] += 1
            continue
        if loc > MAX_LOC:
            rej["too_much_loc"] += 1
            continue
        if loc < MIN_LOC:
            rej["too_little_loc"] += 1
            continue

        # Best-effort: link back to an issue if the PR body mentions one.
        linked_issues = list(collect_issue_refs(pr.title) |
                             collect_issue_refs(pr.body or ""))

        candidates.append({
            "task_source": "pr",
            "pr_number": pr.number,
            "pr_title": pr.title,
            "pr_url": pr.html_url,
            "pr_body": (pr.body or "")[:2000],
            "pr_merge_commit": pr.merge_commit_sha,
            "loc_touched": loc,
            "files_touched": file_paths,
            "linked_issue_numbers": linked_issues,
        })
        print(f"  candidate PR #{pr.number}: {pr.title[:60]}")

    out = Path("candidates.json")
    out.write_text(json.dumps(candidates, indent=2))

    print("\n===== RESULT =====")
    print(f"Candidates written to {out}: {len(candidates)}")
    print(f"Total closed PRs inspected: {seen}")
    print("Rejections by reason:")
    for k, v in sorted(rej.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nRemaining API requests this hour: {show_rate_limit(gh)}")


if __name__ == "__main__":
    main()