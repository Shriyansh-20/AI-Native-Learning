# Failure Analysis

## Summary

5 / 40 batches had incorrect latent-state predictions.

Accuracy: 87.5%

All corrupted batches were detected:
S4 recall = 100%

The five failures were concentrated in Healthy and Benign Drift.

---

## Failure Mode 1 — Prior Bias Toward Healthy

Affected: Batch 6, Batch 32

In both cases, the LLM assigned its highest likelihood to the
correct state, S2_BENIGN_DRIFT.

Batch 6:
P(E|Healthy) = 0.25
P(E|Drift)   = 0.80

Batch 32:
P(E|Healthy) = 0.15
P(E|Drift)   = 0.80

However, the assumed prior strongly favors Healthy:

P(Healthy) = 0.75
P(Drift)   = 0.12

After Bayesian updating, Healthy became the most probable state.

Batch 6:
Healthy 57.08% vs Drift 29.22%

Batch 32:
Healthy 45.73% vs Drift 39.02%

### Takeaway

These are not primarily LLM interpretation failures.

They expose sensitivity to the assumed prior.

The healthy-skewed experimental prior can overpower evidence
supporting less common states.

### Improvement

Estimate priors from historical labelled batches and perform
prior-sensitivity experiments.

---

## Failure Mode 2 — Isolated Critical Signals Were Overweighted

Affected: Batch 25, Batch 38

Both batches were labelled Healthy but contained one null receiver
among 100 records.

No other major anomaly was detected.

Despite this, the LLM assigned:

Batch 25:
P(E|Corrupted) = 0.85

Batch 38:
P(E|Corrupted) = 0.85

The resulting corruption posteriors were 48.24% and 60.80%.

### Takeaway

The reasoner appears to treat the presence of a null receiver as
strong corruption evidence without sufficiently accounting for its
prevalence (1/100) and the otherwise healthy batch.

### Improvement

Make anomaly prevalence and surrounding evidence explicit in the
reasoning prompt.

For example:

"Consider not only whether an anomaly exists, but its frequency,
severity, co-occurring signals, and whether the remainder of the
batch is internally consistent."

---

## Failure Mode 3 — Drift Requires Operational Context

Affected: Batch 24

Evidence included:

- 57 lowercase currencies
- median amount 5322.94
- distribution surge
- one null receiver

The true state was Benign Drift, but the initial posterior ranked
Corrupted highest at 36.70%.

Additional contextual evidence explaining the currency change,
amount surge, and null field changed the belief to:

Benign Drift: 65.59%
Corrupted:     4.37%

### Takeaway

Batch statistics alone may not distinguish legitimate real-world
change from pipeline corruption.

Producer context, deployment history, business events, or human
review can provide high-information evidence.

This motivates the sequential evidence / belief-update loop in the
architecture.

---

# Policy Behaviour Under Inference Failure

Importantly, none of the five inference errors directly caused an
aggressive REJECT decision.

| Batch | Inference Error | Action | Realized Cost |
|---|---|---|---:|
| 6 | Drift → Healthy | REPAIR | ₹2,500 |
| 24 | Drift → Corrupted | ISOLATE | ₹5,000 |
| 25 | Healthy → Corrupted | ISOLATE | ₹7,000 |
| 32 | Drift → Healthy | REPAIR | ₹2,500 |
| 38 | Healthy → Corrupted | ISOLATE | ₹7,000 |

The cost-sensitive layer therefore partially contained errors made
by the inference layer.

This illustrates why the project evaluates both state inference and
decision cost.

A wrong state prediction does not necessarily imply the worst
possible decision.

---

# Improvements Identified

1. Estimate priors from real historical data rather than assuming them.
2. Evaluate sensitivity to different priors.
3. Include anomaly prevalence, not only anomaly presence, in LLM reasoning.
4. Incorporate operational context such as deployments and business events.
5. Calibrate LLM likelihood estimates on a larger labelled dataset.
6. Expand beyond the current 40 synthetic batches.
7. Use human review / additional evidence when posterior uncertainty remains high.
