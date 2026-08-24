# Failure Analysis

## Overall Performance

The final **LLM + Bayesian Agent** was evaluated on **40 synthetic payment-data batches**.

| Metric | Result |
|---|---:|
| Accuracy | **87.5%** |
| Macro Precision | **88.5%** |
| Macro Recall | **85.4%** |
| Macro F1 | **83.8%** |

### Performance by State

| State | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `S1_HEALTHY` | 91.7% | 91.7% | 91.7% | 24 |
| `S2_BENIGN_DRIFT` | 100.0% | **50.0%** | 66.7% | 6 |
| `S3_FORMAT_GLITCH` | 100.0% | **100.0%** | 100.0% | 5 |
| `S4_CORRUPTED` | 62.5% | **100.0%** | 76.9% | 5 |

The system correctly inferred **35 of 40 batches**.

Two results stand out:

- All **5/5 corrupted batches were detected**, giving corruption recall of **100%**.
- `S2_BENIGN_DRIFT` was the hardest state, with only **50% recall**.

Because the dataset contains only 40 synthetic cases, these results describe this experiment and should not be interpreted as production guarantees.

---

## Where Did the Agent Fail?

The five incorrect state predictions were:

| Batch | Ground Truth | Predicted | Top Posterior | Action |
|---|---|---|---:|---|
| 6 | Benign Drift | Healthy | 57.08% | REPAIR |
| 24 | Benign Drift | Corrupted | 36.70% | ISOLATE |
| 25 | Healthy | Corrupted | 48.24% | ISOLATE |
| 32 | Benign Drift | Healthy | 45.73% | REPAIR |
| 38 | Healthy | Corrupted | 60.80% | ISOLATE |

Examining these traces revealed three recurring failure modes.

---

## Failure Mode 1 — The Prior Can Overpower the Evidence

**Affected batches:** 6 and 32

Both batches were actually `S2_BENIGN_DRIFT`.

Interestingly, the LLM assigned its highest likelihood to the **correct state** in both cases:

| Batch | `P(E \| Healthy)` | `P(E \| Drift)` |
|---|---:|---:|
| 6 | 0.25 | **0.80** |
| 32 | 0.15 | **0.80** |

However, the experimental prior strongly favors Healthy:

```text
Healthy        75%
Benign Drift   12%
Format Glitch   8%
Corrupted       5%
```

After Bayesian updating, Healthy became the most probable state.

This shows that the assumed prior can materially influence the final inference.

### Improvement

Estimate priors from historical labelled data and test the system under alternative priors rather than relying on a single assumed distribution.

---

## Failure Mode 2 — Isolated Critical Signals Were Overweighted

**Affected batches:** 25 and 38

Both batches were labelled `S1_HEALTHY`.

Each contained only **one null receiver among 100 records**, while the remaining extracted signals were normal:

- no negative amounts,
- no overflow values,
- no format anomalies,
- no currency shift,
- no distribution surge.

Despite this, the LLM assigned:

```text
P(Evidence | Corrupted) = 0.85
```

in both cases.

The resulting corruption posteriors were:

- Batch 25 → **48.24%**
- Batch 38 → **60.80%**

This suggests that the reasoner gave too much weight to the presence of a critical anomaly without sufficiently considering its **prevalence and surrounding evidence**.

### Improvement

Make anomaly rates explicit and instruct the reasoner to consider:

**frequency + severity + co-occurring signals + overall batch consistency**

rather than only whether an anomaly exists.

---

## Failure Mode 3 — Drift Can Require Operational Context

**Affected batch:** 24

Batch 24 contained competing signals:

```text
57 lowercase currencies
High median amount
Distribution surge
1 null receiver
```

The true state was `S2_BENIGN_DRIFT`, but the initial posterior ranked `S4_CORRUPTED` highest at **36.70%**.

We then introduced additional experimental context explaining that:

- the lowercase currencies came from an intentional producer change,
- the amount surge came from a legitimate promotion,
- the null receiver came from an optional legacy field.

After sequential belief updating:

| State | Before | After |
|---|---:|---:|
| Benign Drift | 30.58% | **65.59%** |
| Corrupted | 36.70% | **4.37%** |

This suggests that batch statistics alone may sometimes be insufficient to distinguish legitimate operational change from corruption.

### Improvement

Allow the agent to incorporate additional evidence such as deployment history, producer context, business events, human review, or new validation results.

This motivates the **new-evidence / belief-update loop** in the architecture.

---

## Did Incorrect Inference Lead to Bad Actions?

Not necessarily.

The five incorrect state predictions resulted in:

| Batch | State Error | Action | Realized Simulated Cost |
|---|---|---|---:|
| 6 | Drift → Healthy | REPAIR | ₹2,500 |
| 24 | Drift → Corrupted | ISOLATE | ₹5,000 |
| 25 | Healthy → Corrupted | ISOLATE | ₹7,000 |
| 32 | Drift → Healthy | REPAIR | ₹2,500 |
| 38 | Healthy → Corrupted | ISOLATE | ₹7,000 |

None of the five inference failures resulted in an automatic `REJECT`.

This happens because the agent does not directly map:

```text
Predicted State → Action
```

Instead, it evaluates expected loss across the **full posterior belief**.

This helped contain some inference errors through more cautious actions such as `REPAIR` and `ISOLATE`.

---

## Decision-Level Result

State accuracy is only one part of the evaluation because the system is ultimately a **decision agent**.

| System | Total Simulated Cost |
|---|---:|
| Naive ACCEPT | ₹5,013,700 |
| Strict Reject | ₹502,500 |
| **LLM + Bayesian Agent** | **₹68,800** |

The final system reduced simulated cost by:

- **98.6%** compared with Naive ACCEPT
- **86.3%** compared with Strict Reject

These values come from the experimental cost matrix and should be interpreted as **simulated relative decision costs**, not measured financial savings.

---

## Key Improvements Identified

The failure analysis suggests four main improvements:

1. **Learn priors from historical data** rather than assuming them.
2. **Represent anomaly prevalence explicitly**, not only anomaly presence.
3. **Use operational context** when drift and corruption are difficult to distinguish.
4. **Evaluate likelihood calibration and generalization** on a larger labelled dataset.

---

## Takeaway

The five failures were not all simply "LLM mistakes."

They came from different parts of the reasoning system:

```text
Batches 6, 32
        ↓
Prior assumption
overpowered drift evidence

Batches 25, 38
        ↓
Isolated anomaly
overweighted by LLM

Batch 24
        ↓
Insufficient
operational context
```

The experiment therefore highlights why the system separates:

**Evidence Interpretation → Belief Updating → Decision Policy**

The agent achieved **87.5% state accuracy**, but more importantly, the expected-loss policy could still make cautious decisions when the most likely state was wrong.
