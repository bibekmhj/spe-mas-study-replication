"""Enumerate candidate bug-fix tasks for the study task set (Protocol v6).

Target repository: pallets/click
Changes from v5: target repository changed from prompt-toolkit/python-prompt-toolkit
to pallets/click for better test-discipline in bug-fix PRs. IMPL_EXCLUDE_PATTERNS
retargeted to click's platform-specific and shell-completion modules.

Selection: merged PRs whose title matches bug-fix language, whose diff is
3-300 LOC across at most 4 files, excluding platform/shell-completion
implementation files, requiring at least one test file to be present in the
diff so the run-time correctness oracle exists.
"""
import json
import os
import re
import time
from pathlib import Path

from github import Github, Auth, RateLimitExceededException, GithubException

REPO = "pallets/click"
CUTOFF_DATE = "2027-01-01"
BUG_TITLE_PATTERNS = [
    r"\bfix(?:e[sd])?\b", r"\bbug\b", r"\bresolv(?:e|es|ed)\b",
    r"\bcorrect(?:s|ed)?\b", r"\brepair\b", r"\bpatch(?:es|ed)?\b",
    r"\bissue\b", r"\bregression\b", r"\bbroken\b", r"\bcrash\b",
    r"\berror\b", r"\bfail(?:s|ed|ure)?\b",
]
# Click-specific implementation exclusions: files whose behavior depends
# strongly on terminal or shell environment and whose tests are less reliable
# in a portable execution environment.
IMPL_EXCLUDE_PATTERNS = [
    r"(?:^|/)_termui_impl\.py$",
    r"(?:^|/)_winconsole\.py$",
    r"(?:^|/)shell_completion\.py$",
]
NONCODE_PATTERNS = [
    r"^docs/", r"^examples/", r"^CHANGELOG", r"^README",
    r"\.md$", r"\.rst$", r"^\.github/",
]
MAX_LOC = 300
MAX_FILES = 4
MIN_LOC = 3
BUG_TITLE_RE = re.compile("|".join(BUG_TITLE_PATTERNS), re.IGNORECASE)


def is_impl_excluded(path):
    return any(re.search(p, path) for p in IMPL_EXCLUDE_PATTERNS)


def is_noncode(path):
    return any(re.search(p, path) for p in NONCODE_PATTERNS)


def is_test_file(path):
    p = Path(path)
    normalized = path.replace("\\", "/")
    return (
        "/tests/" in ("/" + normalized)
        or normalized.startswith("tests/")
        or p.name.startswith("test_")
        or p.name.endswith("_test.py")
    )


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

    print(f"Enumerating all closed PRs from {REPO}...")
    pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

    candidates = []
    rej = {"not_merged": 0, "not_bug_title": 0, "too_many_files": 0,
           "too_much_loc": 0, "too_little_loc": 0,
           "impl_excluded_path": 0, "no_test_file": 0,
           "no_code_files": 0, "error": 0}
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

        code_files = [p for p in file_paths if not is_noncode(p)]
        if not code_files:
            rej["no_code_files"] += 1
            continue

        if any(is_impl_excluded(p) for p in file_paths):
            rej["impl_excluded_path"] += 1
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

        test_files = [p for p in file_paths if is_test_file(p)]
        if not test_files:
            rej["no_test_file"] += 1
            continue

        candidates.append({
            "task_source": "pr",
            "pr_number": pr.number,
            "pr_title": pr.title,
            "pr_url": pr.html_url,
            "pr_body": (pr.body or "")[:2000],
            "pr_merge_commit": pr.merge_commit_sha,
            "loc_touched": loc,
            "files_touched": file_paths,
            "test_files_touched": test_files,
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