"""Single-assistant workflow harness.

Runs one task under the SA condition against the PRE-FIX state of the
repository (parent of the reference PR's merge commit), with the test
file(s) added or modified by the reference PR restored into the working
tree so they serve as the correctness oracle.

Multi-line operator input: paste any number of lines, then a line
containing only END, then enter.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-sonnet-5"
MAX_TOKENS = 4096
MAX_ITERATIONS = 25

SA_SYSTEM_PROMPT = """You are an expert Python software engineer working
in the prompt-toolkit repository. You will fix a specific bug described
in the task below. You may propose code edits and shell commands (e.g.,
pytest invocations). The human operator will approve, edit, or reject
each proposal before it is applied. When you believe the bug is fixed
and tests pass, say DONE."""


# ---------- I/O helpers ----------

def read_multiline(prompt):
    print(prompt)
    print("(end input with a line containing only END and press enter)")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def load_task(task_list_path, task_id):
    tasks = json.loads(Path(task_list_path).read_text())
    for t in tasks:
        if t["task_id"] == task_id:
            return t
    raise SystemExit(f"Task {task_id} not found in {task_list_path}")


def normalize_task(task):
    return {
        "id_number": task.get("pr_number") or task.get("issue_number"),
        "title": task.get("pr_title") or task.get("issue_title", ""),
        "url": task.get("pr_url") or task.get("issue_url", ""),
        "body": task.get("pr_body") or task.get("issue_body", ""),
    }


def log(run_dir, event_type, payload):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "payload": payload,
    }
    with (run_dir / "log.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------- Repo/test helpers ----------

def resolve_parent_commit(repo_path, task, override=None):
    """Return the pre-fix commit for this task."""
    if override:
        return override
    merge = task.get("pr_merge_commit")
    if not merge:
        raise SystemExit(
            f"Task has no pr_merge_commit; cannot compute parent commit."
        )
    r = subprocess.run(
        ["git", "rev-parse", f"{merge}^1"],
        cwd=repo_path, capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def is_test_file(path):
    p = Path(path)
    return (
        "tests/" in path.replace("\\", "/")
        or p.name.startswith("test_")
        or p.name.endswith("_test.py")
    )


def reset_repo(repo_path, commit_hash):
    subprocess.run(
        ["git", "reset", "--hard", commit_hash],
        cwd=repo_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=repo_path, check=True, capture_output=True,
    )


def prepare_task(repo_path, task, parent_commit):
    """Reset repo to parent commit and restore reference-PR test files
    into the working tree (untracked). Returns the list of restored test
    file paths."""
    reset_repo(repo_path, parent_commit)
    files = task.get("files_touched", []) or []
    test_files = [f for f in files if is_test_file(f)]
    restored = []
    for tf in test_files:
        r = subprocess.run(
            ["git", "show", f"{task['pr_merge_commit']}:{tf}"],
            cwd=repo_path, capture_output=True, text=True,
        )
        if r.returncode != 0:
            continue  # test file might not exist in merge commit
        target = Path(repo_path) / tf
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(r.stdout)
        restored.append(tf)
    return restored


def run_pytest_on(repo_path, targets):
    """Run pytest on specific paths (or full suite if targets is empty)."""
    args = ["pytest", "-x", "-q"]
    if targets:
        args += targets
    r = subprocess.run(
        args, cwd=repo_path, capture_output=True, text=True, timeout=600,
    )
    return r.returncode == 0, r.stdout + r.stderr


def run_ruff(repo_path, changed_files):
    if not changed_files:
        return ""
    r = subprocess.run(
        ["ruff", "check"] + changed_files,
        cwd=repo_path, capture_output=True, text=True, timeout=60,
    )
    return r.stdout + r.stderr


def git_diff(repo_path):
    r = subprocess.run(
        ["git", "diff"], cwd=repo_path, capture_output=True, text=True, timeout=30,
    )
    return r.stdout


def get_git_changed_files(repo_path):
    r = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_path, capture_output=True, text=True, timeout=30,
    )
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--task-list", default="task_list.json")
    ap.add_argument("--repo", default="repo")
    ap.add_argument(
        "--commit-override", default=None,
        help="Optional: override the derived parent commit (for debugging).",
    )
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()

    task = load_task(args.task_list, args.task_id)
    t = normalize_task(task)
    run_dir = Path(args.runs_dir) / f"{args.task_id}_SA_rep{args.rep}"
    run_dir.mkdir(parents=True, exist_ok=True)

    parent_commit = resolve_parent_commit(args.repo, task, args.commit_override)
    test_files = prepare_task(args.repo, task, parent_commit)

    log(run_dir, "config", {
        "task_id": args.task_id, "condition": "SA", "rep": args.rep,
        "model": MODEL, "parent_commit": parent_commit,
        "merge_commit": task.get("pr_merge_commit"),
        "id_number": t["id_number"],
        "oracle_test_files": test_files,
        "files_touched": task.get("files_touched", []),
    })

    # Baseline: does the oracle fail at the parent commit? (Should, for real bugs.)
    if test_files:
        baseline_pass, baseline_out = run_pytest_on(args.repo, test_files)
    else:
        baseline_pass, baseline_out = None, "no oracle test files identified"
    log(run_dir, "baseline_test_run",
        {"oracle_pass": baseline_pass, "output": baseline_out[-2000:] if isinstance(baseline_out, str) else ""})

    print(f"\n=== TASK {args.task_id} SETUP ===")
    print(f"parent_commit: {parent_commit}")
    print(f"merge_commit:  {task.get('pr_merge_commit')}")
    print(f"oracle tests:  {test_files if test_files else '(none — will use full suite)'}")
    print(f"baseline oracle result: "
          f"{'PASS (WARNING: no bug detected at parent commit)' if baseline_pass else 'FAIL (bug is reproducible)' if baseline_pass is False else 'N/A'}")

    if baseline_pass is True:
        proceed = input(
            "\nBaseline tests already pass; the bug is not reproducible at "
            "the parent commit. Continue anyway? (y/N): "
        ).strip().lower()
        if proceed != "y":
            log(run_dir, "summary",
                {"outcome": "skipped_no_reproducible_bug",
                 "iterations": 0, "wall_clock_s": 0,
                 "tokens_in": 0, "tokens_out": 0})
            print("Skipped. Consider picking a different task.")
            return

    client = Anthropic()
    messages = [{
        "role": "user",
        "content": (
            f"Fix the bug described in the following task.\n\n"
            f"Reference PR or issue #{t['id_number']}: {t['title']}\n"
            f"URL: {t['url']}\n\n"
            f"Description:\n{t['body']}\n\n"
            f"Repository is at {args.repo}. Test files that describe the "
            f"expected behavior are already present in the working tree. "
            f"Use pytest to run tests. Propose edits or shell commands one "
            f"at a time and I will apply them. Do NOT modify test files."
        ),
    }]

    start = time.time()
    tokens_in_total = tokens_out_total = 0
    iteration = 0
    outcome = "unknown"

    while iteration < MAX_ITERATIONS:
        iteration += 1
        response = client.messages.create(
            model=MODEL, system=SA_SYSTEM_PROMPT,
            messages=messages, max_tokens=MAX_TOKENS,
        )
        assistant_text = next(
            (b.text for b in response.content if hasattr(b, "text")), ""
        )
        thinking_text = "\n".join(
            getattr(b, "thinking", "") for b in response.content
            if not hasattr(b, "text")
        )
        tokens_in_total += response.usage.input_tokens
        tokens_out_total += response.usage.output_tokens
        log(run_dir, "assistant_message", {
            "iteration": iteration, "text": assistant_text,
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens,
        })
        if thinking_text:
            log(run_dir, "assistant_thinking",
                {"iteration": iteration, "text": thinking_text})

        print(f"\n--- iteration {iteration} ---")
        print(assistant_text)
        print()

        words = assistant_text.split()
        if words and "DONE" in words[-5:]:
            oracle_pass, oracle_out = run_pytest_on(args.repo, test_files)
            outcome = "pass" if oracle_pass else "fail_tests"
            log(run_dir, "final_oracle_test",
                {"passed": oracle_pass, "output": oracle_out[-2000:]})
            break

        user_action = input(
            "\nAction: (a)pply as-is, (e)dit, (r)eject, (t)ests, "
            "(f)inish (mark done and run tests), (x) abort: "
        ).strip().lower()

        if user_action == "x":
            outcome = "abort"
            log(run_dir, "human_intervention", {"type": "abort"})
            break
        if user_action == "f":
            oracle_pass, oracle_out = run_pytest_on(args.repo, test_files)
            outcome = "pass" if oracle_pass else "fail_tests"
            log(run_dir, "final_oracle_test",
                {"passed": oracle_pass, "output": oracle_out[-2000:]})
            break
        if user_action == "t":
            oracle_pass, oracle_out = run_pytest_on(args.repo, test_files)
            log(run_dir, "human_intervention",
                {"type": "run_tests", "oracle_pass": oracle_pass})
            messages.append({"role": "assistant", "content": assistant_text})
            messages.append({"role": "user",
                             "content": f"Test output:\n{oracle_out[-1500:]}"})
            continue

        note = input("Note (optional, single line): ").strip()
        log(run_dir, "human_intervention", {"type": user_action, "note": note})

        if user_action == "a":
            applied_result = read_multiline("Result of applying (paste output):")
            messages.append({"role": "assistant", "content": assistant_text})
            messages.append({"role": "user",
                             "content": f"Applied. Result:\n{applied_result}"})
        elif user_action == "e":
            edited_text = read_multiline("Paste your edited version:")
            messages.append({"role": "assistant", "content": assistant_text})
            messages.append({"role": "user",
                             "content": f"I made changes: {edited_text}"})
        elif user_action == "r":
            reason = read_multiline("Reason for reject:")
            messages.append({"role": "assistant", "content": assistant_text})
            messages.append({"role": "user",
                             "content": f"Rejected. Reason: {reason}"})

    if iteration >= MAX_ITERATIONS and outcome == "unknown":
        outcome = "fail_iteration_cap"

    # Regression check: run the full suite too (excluding the untracked oracle
    # tests would be hard; we just report both).
    full_pass, full_out = run_pytest_on(args.repo, [])
    elapsed = time.time() - start
    diff = git_diff(args.repo)
    changed_files = get_git_changed_files(args.repo)
    ruff_out = run_ruff(args.repo, changed_files)

    log(run_dir, "final_full_suite",
        {"passed": full_pass, "output": full_out[-1500:]})
    log(run_dir, "summary", {
        "outcome": outcome, "iterations": iteration,
        "wall_clock_s": elapsed,
        "tokens_in": tokens_in_total, "tokens_out": tokens_out_total,
        "changed_files": changed_files, "diff_lines": len(diff.splitlines()),
        "baseline_oracle_pass": baseline_pass,
        "full_suite_pass_at_end": full_pass,
    })
    (run_dir / "final.diff").write_text(diff)
    (run_dir / "ruff.txt").write_text(ruff_out)

    print(f"\n=== RUN SUMMARY ===")
    print(f"outcome:        {outcome}")
    print(f"iterations:     {iteration}")
    print(f"wall_clock:     {elapsed:.1f}s")
    print(f"tokens:         in={tokens_in_total}, out={tokens_out_total}")
    print(f"baseline pass:  {baseline_pass}")
    print(f"full-suite end: {full_pass}")


if __name__ == "__main__":
    main()