# Student Project — Week 1

## Overview

This repository contains the Week 1 deliverable for the student project in the AI-Native course. It documents the experiment, data, code, and brief findings so you can reproduce and understand what we've done so far.

## What we completed
- Implemented a simple agent and environment prototype in `src/agent.py` and `src/environment.py`.
- Created a small test dataset in `data/test_batches.json` used for quick experiment runs.
- Added an experiment script `experiments/run_experiment.py` to run the agent on the dataset and produce results.
- Drafted a short report and discussion artifacts under `paper/` and `social/`.

## Repository structure

- `src/` — core code: `agent.py`, `environment.py`.
- `data/` — input data used by experiments (`test_batches.json`).
- `experiments/` — runnable experiment scripts (`run_experiment.py`).
- `paper/` — LaTeX source of the paper, bibliography, and figures.
- `results/` — generated outputs from experiments (metrics, logs, saved models).
- `decisions/` — decision records and notes.
- `social/` — short-format posts (LinkedIn, X/Twitter drafts).
- `README.md` — this file.

## How to run (quick)

1. Open a terminal in this folder:

```bash
cd week1/deliverables/student-project
```

2. Run the experiment script (requires Python 3.8+):

```bash
python3 experiments/run_experiment.py
```

Notes:
- The script is written for a small local dataset (`data/test_batches.json`) so it should run quickly without extra dependencies.
- If the script imports modules from `src/`, run it from the project root as shown above so Python finds `src` on the path.

## Findings (so far)

- The prototype agent completes basic interactions with the environment and logs results to `results/`.
- Initial experiment runs are primarily sanity checks; no final evaluation yet.

## Next steps

1. Add a requirements file and document dependencies.
2. Improve experiment logging and provide a small evaluation script.
3. Expand the dataset and run longer experiments; capture and summarize metrics in `results/`.

## Contact / Notes
If anything here looks off or you want the README expanded (e.g., add dependency list, usage examples, or run flags), tell me what to include and I will update it.

## Dataset creation (how we made `data/test_batches.json`)

We generate synthetic, labeled batches with `src/environment.py` using `generate_batch` and `generate_test_suite`.

- Each batch contains 100 synthetic transactions with fields: `transaction_id`, `timestamp`, `sender_account`, `receiver_account`, `amount`, `currency`, and `status`.
- The environment supports four hidden states (used as ground truth for evaluation): `S1_HEALTHY`, `S2_BENIGN_DRIFT`, `S3_FORMAT_GLITCH`, `S4_CORRUPTED`.
- `generate_test_suite()` produces 40 batches with a controlled distribution (24 healthy, 6 benign drift, 5 format glitch, 5 corrupted) and writes them to `data/test_batches.json`.

State-specific generation behaviors:
- `S1_HEALTHY`: normal transactional data (clean timestamps, typical amounts, uppercase currency, trimmed status).
- `S2_BENIGN_DRIFT`: legitimate volume/amount surge (amounts scaled ~3.2x) and occasional lowercase currency tokens (``inr``) to simulate non-critical drift.
- `S3_FORMAT_GLITCH`: recoverable format issues such as dates in `DD/MM/YYYY` format and padded status strings (`" SUCCESS "`).
- `S4_CORRUPTED`: critical semantic corruption introduced rarely: negative amounts, extreme overflow amounts, or `null` receiver accounts.

## Cases we handle (evidence extracted)

The agent's `extract_evidence` (in `src/agent.py`) looks for indicators used to form a compact evidence vector:
- Negative amounts, extreme overflows, or null receivers -> flagged as `has_critical_error`.
- Date formats like `DD/MM/YYYY` or extra whitespace in `status` -> flagged as `has_format_error`.
- Large median amounts or lowercase currency -> flagged as `has_distribution_surge`.

These flags are used to compute likelihoods for each hidden state (see `compute_likelihood`). The heuristics map common problems to higher likelihoods for particular states (e.g., `has_critical_error` strongly points to `S4_CORRUPTED`).

## No LLM API — how decisions are made

We do not call any external LLM APIs for triage. Decision making is fully algorithmic and local:

1. Extract evidence from a batch using `PaymentTriageAgent.extract_evidence(records)`.
2. Compute per-state likelihoods with `compute_likelihood(evidence, state)`.
3. Multiply the per-state likelihoods by the prior (`self.prior`) and normalize to get a posterior belief over states (`update_belief`).
4. Compute expected loss per action using the `COST_MATRIX` and pick the action that minimizes expected loss (`decide_action`).

This is a Bayesian triage pipeline (prior -> likelihood -> posterior -> decision) implemented deterministically in `src/agent.py`.

## How we decide where to place/label a current batch (assigning a hidden state)

The environment provides `true_state` only for testing and evaluation. In production or streaming runs, we infer a batch's most likely hidden state from the agent's posterior belief.

Simple tagging rules we use or recommend:
- Argmax tag: `assigned_state = max(belief, key=belief.get)` — tag the batch with the highest posterior probability.
- Threshold tagging: if `belief['S4_CORRUPTED'] > 0.5` then label as `S4_CORRUPTED`; otherwise if `max(belief.values()) > 0.6` assign argmax; otherwise mark as `UNSURE` and `ISOLATE` for human review.

Example (pseudo-code):

```python
evidence = agent.extract_evidence(records)
belief = agent.update_belief(evidence)
assigned = max(belief, key=belief.get)
if belief['S4_CORRUPTED'] > 0.5:
	# strong corruption signal
	label = 'S4_CORRUPTED'
elif belief[assigned] > 0.6:
	label = assigned
else:
	label = 'ISOLATE'  # conservative fallback
```

Why use thresholds/fallbacks:
- Posterior probabilities quantify uncertainty. Using a threshold avoids overconfident mislabels when evidence is ambiguous.
- Conservative actions like `ISOLATE` or manual review help avoid costly errors (see the `COST_MATRIX` penalties in `src/agent.py`).

If you'd like, I can add a small helper function (e.g., `tag_batch(records, agent, thresholds)`) and examples to the repo to demonstrate automated labeling and safe fallbacks.
