# Replication Package: SA vs Human-Supervised MA Coding Workflows on `pallets/click`

This repository contains the replication package for the paper
*"Single-Assistant versus Human-Supervised Multi-Agent Workflows for
Software Bug Fixing: A Reproducible Controlled Comparison on
pallets/click"* by Bibek Maharjan, submitted to the Special Issue on
AI-Native Software Engineering, Software: Practice and Experience (2027).

## Layout

```
.
|-- README.md                    (this file)
|-- LICENSE                      (MIT)
|-- requirements.txt             (pinned Python packages)
|-- protocol_version.txt         (task-selection protocol version)
|-- tool_versions.txt            (exact versions of Python, ruff, mypy, pytest)
|-- frozen_commit.txt            (the pallets/click commit hash all runs used)
|-- candidates.json              (the 80-candidate pool produced by enumeration)
|-- task_list.json               (the 15 drawn tasks with PR # and merge-commit)
|-- scripts/                     (task-selection scripts, SA and MA runners)
|-- prompts/                     (system and role prompts used verbatim)
|-- runs/                        (per-run logs for all 48 completed runs)
|-- results/                     (computed tables and analysis outputs)
```

The `repo/` subfolder used during execution (a local clone of
`pallets/click` at the frozen commit) is intentionally NOT included
here. See "Reproducing the study" below for how to obtain it.

## Environment

- Python 3.14 (see `tool_versions.txt` for the exact patch version)
- Anthropic Python SDK 1.4.0 (see `requirements.txt`)
- ruff, mypy, and pytest at the versions pinned in `tool_versions.txt`
  and `requirements.txt`
- An Anthropic API key with access to `claude-sonnet-5`, exported as
  the environment variable `ANTHROPIC_API_KEY`. Do NOT commit the key
  to any repository.

## Reproducing the study

1. Clone this repository. Create a Python 3.14 virtualenv and install
   the pinned packages:

   ```
   python3.14 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Clone `pallets/click` into a `repo/` subfolder of this directory,
   and check out the frozen commit hash recorded in
   `frozen_commit.txt`:

   ```
   git clone https://github.com/pallets/click.git repo
   cd repo && git checkout $(cat ../frozen_commit.txt) && cd ..
   ```

3. Set your API key:

   ```
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

4. (Optional) Regenerate `candidates.json` and `task_list.json` from
   GitHub using the scripts under `scripts/`. The frozen versions of
   both files are included in this repository, so you can skip this
   step and reproduce against the exact task set the paper reports.

5. Execute the runs. For each task in `task_list.json`, and each
   condition (SA, MA) and repetition (1, 2), invoke the corresponding
   runner under `scripts/`. The runners record full transcripts,
   extended-thinking content, tool calls, per-intervention timestamps,
   final diffs, oracle-test outputs, static-analysis outputs, and
   token accounting into the corresponding folder under `runs/`.

6. Regenerate the numbers reported in Section 4 of the paper using
   the analysis scripts under `scripts/` (or under `results/`,
   whichever the file layout places them).

The full run of all 48 conditions used approximately US$30.86 in API
cost on Anthropic's Claude Sonnet 5 at the published pricing at the
time of the study, and approximately 20 hours of wall-clock time with
human-in-the-loop operator time on the reference toolchain.

## Contents of `runs/`

There are 48 folders under `runs/`, one per completed run, named
`TXX_[SA|MA]_repY` for task X, condition [SA or MA], and repetition Y.
Three tasks from the drawn set (T09, T11, T14) were skipped at run
start when the baseline pytest invocation on the oracle test files
reported pass at the parent commit, indicating the reference bug was
not reproducible under the pinned toolchain; those three tasks have no
run folders. Each present run folder contains at minimum a
`log.jsonl` transcript of the full run.

Personal filesystem paths were sanitized from the `log.jsonl` files
before publication. Occurrences of the local absolute paths were
replaced with the placeholders `<REPO_ROOT>` and `<STUDY_ROOT>`.
A small number of `/home/user/...` strings that appear in the
transcripts are model-generated placeholder paths from early model
iterations and were left as-is.

## Reproducibility notes

- **Model behavior can drift.** The exact model identifier and per-run
  date are logged in each run folder. Re-execution against a later
  model version is possible but expected to produce different numbers;
  document the version you ran against.
- **Sampling parameters are not user-configurable** for
  `claude-sonnet-5` through the Anthropic Python SDK version used.
  `temperature` and `top_p` are rejected as deprecated. Stochasticity
  is characterized empirically via K = 2 repetitions per (task,
  condition) cell.
- **Pytest environment.** All runs invoke pytest as
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest ...` to isolate
  from system-installed plugins. Do the same in your environment.
- **Pre-existing pytest collection error.** At the frozen commit,
  `tests/test_basic.py` in the target repository produces a
  `PytestRemovedIn10Warning` collection error unrelated to any
  agent's fix. This causes the full-suite pytest pass check to report
  `False` on every run irrespective of the agent's output. The oracle-
  tests-pass metric (the primary outcome for RQ1) is unaffected
  because it targets specific test files rather than the whole suite.

## Data availability

This repository is the primary data-availability artifact for the
paper. It will be archived at Zenodo with a persistent DOI on
acceptance; the archived version will be linked from the published
paper's Data Availability statement.

## Ethics and conflict of interest

The study involves no human participants. No employer data, no
proprietary code, and no identifying information from any third party
enter the study. All materials come from the public `pallets/click`
repository and the author's own experimental scripts and logs.

The author is a software engineer at JPMorgan Chase & Co. This
research was conducted in the author's personal capacity, outside of
that employment, using no employer data, no employer code, and no
employer infrastructure. Views expressed in the paper and in this
repository are the author's personal views and do not necessarily
reflect the views of JPMorgan Chase & Co. or any of its affiliates.

The author is not a contributor to the `pallets/click` repository and
has no financial or advisory relationship with the Pallets project
maintainers or with Anthropic.

## License

MIT. See `LICENSE`. The target repository (`pallets/click`) is
BSD-3-Clause; this package does not redistribute click's source, only
per-run diffs against public commits.

## Contact

Bibek Maharjan (bbkmhj06@gmail.com, ORCID 0009-0001-9745-6375).
