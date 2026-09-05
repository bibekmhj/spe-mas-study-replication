"""Draw the study task list from candidates.json using a fixed seed."""
import json
import random
from pathlib import Path

SEED_TASK_DRAW = 42
SEED_HOLDOUT = 137
N_TASKS = 15
N_HOLDOUT = 4

def main():
    candidates = json.loads(Path("candidates.json").read_text())
    print(f"Candidate pool size: {len(candidates)}")
    if len(candidates) < 30:
        raise SystemExit(
            f"Only {len(candidates)} candidates; needs >= 30. "
            "Relax filters or extend cutoff and re-run enumerate_candidates.py."
        )

    rng = random.Random(SEED_TASK_DRAW)
    drawn = rng.sample(candidates, N_TASKS)
    for i, t in enumerate(drawn):
        t["task_id"] = f"T{i+1:02d}"

    rng2 = random.Random(SEED_HOLDOUT)
    holdout_indices = set(rng2.sample(range(N_TASKS), N_HOLDOUT))
    for i, t in enumerate(drawn):
        t["assignment"] = "holdout" if i in holdout_indices else "training"

    Path("task_list.json").write_text(json.dumps(drawn, indent=2))
    print(f"Wrote {N_TASKS} tasks to task_list.json")
    print(f"  training: {N_TASKS - N_HOLDOUT}; holdout: {N_HOLDOUT}")
    for t in drawn:
        print(f"  {t['task_id']} ({t['assignment']}): #{t['issue_number']} {t['issue_title'][:50]}")

if __name__ == "__main__":
    main()
