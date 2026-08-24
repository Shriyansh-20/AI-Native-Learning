# Data Quality Triage Agent

An experimental agent for **data-quality triage under uncertainty**.

Given a batch of payment records, the agent maintains a belief over four possible hidden states:

- `S1_HEALTHY`
- `S2_BENIGN_DRIFT`
- `S3_FORMAT_GLITCH`
- `S4_CORRUPTED`

and chooses one of:

`ACCEPT` · `REPAIR` · `ISOLATE` · `REJECT`

The goal is to avoid treating every anomaly as a simple binary validation failure.

---

## How It Works

```text
Incoming Batch
      ↓
Evidence Extraction
      ↓
Structured Evidence
      ↓
LLM estimates P(Evidence | State)
      ↓
Bayesian Update
      ↓
P(State | Evidence)
      ↓
Expected-Loss Policy
      ↓
ACCEPT / REPAIR / ISOLATE / REJECT
```

The LLM only interprets the evidence and estimates likelihoods.

Bayesian updating and action selection are deterministic Python calculations.

The action is selected by minimizing:

```text
Expected Loss(action)
= Σ P(State | Evidence) × Cost(action, State)
```

---

## Evaluation

The final experiment uses `data/test_batches_v2.json`:

```text
40 synthetic batches
100 transactions per batch
4,000 transactions total
```

Ground-truth distribution:

| State | Batches |
|---|---:|
| Healthy | 24 |
| Benign Drift | 6 |
| Format Glitch | 5 |
| Corrupted | 5 |

The experiment used `kimi-latest` to estimate the evidence likelihoods.

LLM outputs for the 40 evaluation batches are cached in:

```text
data/llm_likelihood_cache.json
```

---

## Run the Agent

Run commands from `student-project/`.

### Full evaluation

```bash
python3 -m experiments.run_experiment
```

Runs all 40 batches and reports costs, accuracy, precision/recall/F1,
action distribution, confusion matrix, and failure cases.

### Inspect one decision

```bash
python3 -m experiments.inspect_batch 24
```

Replace `24` with any batch ID from `1` to `40`.

This shows the complete trace:

```text
Evidence
  ↓
Prior
  ↓
LLM Likelihoods
  ↓
Posterior
  ↓
Expected Losses
  ↓
Action
```

For example:

```bash
python3 -m experiments.inspect_batch 1
```

shows a healthy case, while Batch 24 shows one of the ambiguous failure cases.

### Test belief updating

```bash
python3 -m experiments.belief_update_demo
```

This demonstrates how new contextual evidence can update an existing posterior and trigger a new expected-loss calculation.

---

## Results

### State Inference

```text
Overall Accuracy: 87.5%
Macro Precision:  88.5%
Macro Recall:     85.4%
Macro F1:         83.8%
Corrupted Recall: 100% (5/5)
```

### Simulated Decision Cost

| System | Cost |
|---|---:|
| Naive Accept | ₹5,013,700 |
| Strict Reject | ₹502,500 |
| **LLM + Bayesian Agent** | **₹68,800** |

This corresponds to a simulated cost reduction of:

- **98.6% vs Naive Accept**
- **86.3% vs Strict Reject**

These costs come from an experimental cost matrix and are **not measured financial savings**.

---

## Example: Updating a Belief

Batch 24 was initially inferred as `S4_CORRUPTED`, although its ground truth was `S2_BENIGN_DRIFT`.

After additional operational context:

| State | Before | After |
|---|---:|---:|
| Benign Drift | 30.58% | **74.73%** |
| Corrupted | 36.70% | **3.16%** |

The inferred state changed substantially, while the minimum-cost action remained `ISOLATE`.

---

## Project Structure

```text
data/
    test_batches_v2.json
    llm_likelihood_cache.json

src/
    agent.py
    llm_inference.py

experiments/
    run_experiment.py
    inspect_batch.py
    belief_update_demo.py

research-file.md
discussion-record.md
failure-analysis.md
paper/
```

---

## More Detail

- `failure-analysis.md` — incorrect predictions and decision traces
- `research-file.md` — research and problem formulation
- `discussion-record.md` — practitioner/community discussions
- `paper/` — complete academic write-up

The benchmark, prior, and cost matrix are experimental constructs. The current results should therefore be interpreted as a controlled prototype rather than evidence of production reliability.
