"""Multi-agent workflow harness.

Runs one task under the MA condition against the PRE-FIX state of the
repository (parent of the reference PR's merge commit), with the test
file(s) added or modified by the reference PR restored into the working
tree so they serve as the correctness oracle.

Four agents: Planner, Coder, Reviewer, Tester. Human checkpoints after
Planner and before commit.

Multi-line operator input: paste any number of lines, then a line
containing only END, then enter.
"""
import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-sonnet-5"
MAX_TOKENS = 4096
MAX_CODER_ITERATIONS = 12

PLANNER_PROMPT = """You are the Planner in a multi-agent bug-fixing team.
Read the task description and repository summary. Produce a concise plan
with:
1. Files you expect to touch.
2. Steps in order.
3. Risks or things you are unsure about.
Do not write code. Do not modify files. Output only the plan."""

CODER_PROMPT = """You are the Coder in a multi-agent bug-fixing team.
Execute the Plan provided by the Planner. Make edits to the repository.
Run pytest after each meaningful change. Stop when tests pass or when
you cannot proceed. Do NOT modify test files."""

REVIEWER_PROMPT = """You are the Reviewer in a multi-agent bug-fixing team.
The Coder has produced a diff. Given the Plan, the diff, and the test
outcome, write review notes. Answer: does the diff implement the Plan?
Is anything stylistically wrong or missing? Are there latent regressions?
Do not modify code; only write review notes."""

TESTER_PROMPT = """You are the Tester in a multi-agent bug-fixing team.
Given the final diff, the pytest output, and the Reviewer's notes,
write a test-rationale artifact: does the existing test suite adequately
demonstrate the fix? Would additional tests be worth adding? If the fix
should be handed back to the Coder for more work, say so."""


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


# ---------- Repo / test helpers ----------

def resolve_parent_commit(repo_path, task, override=None):
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
            continue
        target = Path(repo_path) / tf
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(r.stdout)
        restored.append(tf)
    return restored


def run_pytest_on(repo_path, targets):
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


def call(client, system, user):
    r = client.messages.create(
        model=MODEL, system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=MAX_TOKENS,
    )
    text = next((b.text for b in r.content if hasattr(b, "text")), "")
    return text, r.usage.input_tokens, r.usage.output_tokens


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--task-list", default="task_list.json")
    ap.add_argument("--repo", default="repo")
    ap.add_argument("--commit-override", default=None)
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()

    task = load_task(args.task_list, args.task_id)
    t = normalize_task(task)
    run_dir = Path(args.runs_dir) / f"{args.task_id}_MA_rep{args.rep}"
    run_dir.mkdir(parents=True, exist_ok=True)

    parent_commit = resolve_parent_commit(args.repo, task, args.commit_override)
    test_files = prepare_task(args.repo, task, parent_commit)

    log(run_dir, "config", {
        "task_id": args.task_id, "condition": "MA", "rep": args.rep,
        "model": MODEL, "parent_commit": parent_commit,
        "merge_commit": task.get("pr_merge_commit"),
        "id_number": t["id_number"],
        "oracle_test_files": test_files,
        "files_touched": task.get("files_touched", []),
    })

    if test_files:
        baseline_pass, baseline_out = run_pytest_on(args.repo, test_files)
    else:
        baseline_pass, baseline_out = None, "no oracle test files identified"
    log(run_dir, "baseline_test_run",
        {"oracle_pass": baseline_pass,
         "output": baseline_out[-2000:] if isinstance(baseline_out, str) else ""})

    print(f"\n=== TASK {args.task_id} SETUP ===")
    print(f"parent_commit: {parent_commit}")
    print(f"merge_commit:  {task.get('pr_merge_commit')}")
    print(f"oracle tests:  {test_files if test_files else '(none)'}")
    print(f"baseline oracle result: "
          f"{'PASS (WARNING)' if baseline_pass else 'FAIL (bug reproducible)' if baseline_pass is False else 'N/A'}")
    if baseline_pass is True:
        proceed = input(
            "\nBaseline tests already pass; bug not reproducible at parent. "
            "Continue anyway? (y/N): "
        ).strip().lower()
        if proceed != "y":
            log(run_dir, "summary",
                {"outcome": "skipped_no_reproducible_bug",
                 "iterations": 0, "wall_clock_s": 0,
                 "tokens_in": 0, "tokens_out": 0})
            print("Skipped.")
            return

    client = Anthropic()
    tokens_in_total = tokens_out_total = 0
    iterations = 0
    outcome = "unknown"
    start = time.time()

    # --- PLANNER ---
    task_prompt = (
        f"Reference PR or issue #{t['id_number']}: {t['title']}\n"
        f"URL: {t['url']}\n\n"
        f"Description:\n{t['body']}\n\n"
        f"Note: test files describing expected behavior are already present "
        f"in the working tree. Do NOT modify them."
    )
    plan, ti, to = call(client, PLANNER_PROMPT, task_prompt)
    tokens_in_total += ti; tokens_out_total += to
    iterations += 1
    (run_dir / "plan.md").write_text(plan)
    log(run_dir, "planner_output", {"tokens_in": ti, "tokens_out": to})

    print("\n=== PLAN ===\n" + plan)
    decision = input(
        "\nAccept plan? (a)ccept / (r)evise once / (x) abort: "
    ).strip().lower()
    log(run_dir, "human_intervention",
        {"checkpoint": "post_plan", "decision": decision})
    if decision == "x":
        outcome = "abort_post_plan"
    elif decision == "r":
        note = read_multiline("What should be revised?")
        plan_v2, ti, to = call(
            client, PLANNER_PROMPT,
            task_prompt + f"\n\nRevision request: {note}\nPrior plan:\n{plan}",
        )
        tokens_in_total += ti; tokens_out_total += to
        iterations += 1
        (run_dir / "plan_v2.md").write_text(plan_v2)
        plan = plan_v2

    # --- CODER ---
    if outcome == "unknown":
        coder_iter = 0
        while coder_iter < MAX_CODER_ITERATIONS:
            coder_iter += 1
            current_diff = git_diff(args.repo) or "(no changes yet)"
            passed, test_output = run_pytest_on(args.repo, test_files)
            coder_input = (
                f"Plan:\n{plan}\n\nCurrent diff so far:\n{current_diff}\n\n"
                f"Latest test output:\n{test_output[-1500:]}\n\n"
                f"Continue executing the plan. Propose edits as shell "
                f"commands (sed, cat > file, patch) or paste full-file "
                f"replacements. Say DONE when you believe tests pass."
            )
            coder_out, ti, to = call(client, CODER_PROMPT, coder_input)
            tokens_in_total += ti; tokens_out_total += to
            iterations += 1
            log(run_dir, "coder_iteration",
                {"iter": coder_iter, "text": coder_out,
                 "tokens_in": ti, "tokens_out": to})
            print(f"\n--- Coder iter {coder_iter} ---\n{coder_out}\n")

            action = input(
                "Apply proposal to repo, then (c)ontinue / (d)one / "
                "(x) abort: "
            ).strip().lower()
            if action == "x":
                outcome = "abort_coder"; break
            if action == "d" or "DONE" in coder_out:
                break
        if coder_iter >= MAX_CODER_ITERATIONS and outcome == "unknown":
            outcome = "fail_iteration_cap"

    # --- REVIEWER + TESTER + commit checkpoint ---
    if outcome == "unknown":
        final_diff = git_diff(args.repo)
        passed, test_output = run_pytest_on(args.repo, test_files)
        review_input = (
            f"Plan:\n{plan}\n\nFinal diff:\n{final_diff}\n\n"
            f"Oracle test output:\n{test_output[-1500:]}"
        )
        review, ti, to = call(client, REVIEWER_PROMPT, review_input)
        tokens_in_total += ti; tokens_out_total += to
        iterations += 1
        (run_dir / "review_notes.md").write_text(review)
        log(run_dir, "reviewer_output", {"tokens_in": ti, "tokens_out": to})

        tester_input = (
            f"Final diff:\n{final_diff}\n\n"
            f"Oracle test output:\n{test_output[-1500:]}\n\n"
            f"Reviewer notes:\n{review}"
        )
        tester_out, ti, to = call(client, TESTER_PROMPT, tester_input)
        tokens_in_total += ti; tokens_out_total += to
        iterations += 1
        (run_dir / "test_rationale.md").write_text(tester_out)
        log(run_dir, "tester_output", {"tokens_in": ti, "tokens_out": to})

        print("\n=== REVIEW ===\n" + review)
        print("\n=== TESTER RATIONALE ===\n" + tester_out)
        commit_decision = input(
            "\nCommit? (c)ommit / (b)ack to Coder / (x) abort: "
        ).strip().lower()
        log(run_dir, "human_intervention",
            {"checkpoint": "pre_commit", "decision": commit_decision})
        if commit_decision == "x":
            outcome = "abort_pre_commit"
        elif commit_decision == "c":
            oracle_pass, oracle_out = run_pytest_on(args.repo, test_files)
            outcome = "pass" if oracle_pass else "fail_tests"
            log(run_dir, "final_oracle_test",
                {"passed": oracle_pass, "output": oracle_out[-2000:]})
        else:
            outcome = "back_to_coder_not_executed"

    full_pass, full_out = run_pytest_on(args.repo, [])
    elapsed = time.time() - start
    diff = git_diff(args.repo)
    changed_files = get_git_changed_files(args.repo)
    ruff_out = run_ruff(args.repo, changed_files)

    log(run_dir, "final_full_suite",
        {"passed": full_pass, "output": full_out[-1500:]})
    log(run_dir, "summary", {
        "outcome": outcome, "iterations": iterations,
        "wall_clock_s": elapsed,
        "tokens_in": tokens_in_total, "tokens_out": tokens_out_total,
        "changed_files": changed_files, "diff_lines": len(diff.splitlines()),
        "baseline_oracle_pass": baseline_pass,
        "full_suite_pass_at_end": full_pass,
    })
    (run_dir / "final.diff").write_text(diff)
    (run_dir / "ruff.txt").write_text(ruff_out)
    print(
        f"\n=== RUN SUMMARY ===\noutcome: {outcome}\n"
        f"iterations: {iterations}\nwall_clock: {elapsed:.1f}s\n"
        f"tokens: in={tokens_in_total}, out={tokens_out_total}\n"
        f"baseline pass: {baseline_pass}\n"
        f"full-suite end: {full_pass}"
    )


if __name__ == "__main__":
    main()