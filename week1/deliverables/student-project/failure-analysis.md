# Failure Analysis

## Overview

The final **LLM + Bayesian Data Quality Triage Agent** was evaluated on **40 synthetic payment-data batches**.

The purpose of this analysis is not only to report aggregate accuracy, but to inspect where the system failed, identify which component contributed to each failure, and determine whether incorrect state inference also resulted in poor decisions.

The evaluation revealed three main failure patterns:

1. **The assumed prior can overpower evidence for Benign Drift.**
2. **Isolated critical signals can be overweighted as evidence of corruption.**
3. **Some drift-vs-corruption cases cannot be resolved from batch statistics alone and require operational context.**

Importantly, incorrect state inference did not always translate into the worst action because the final decision was made separately using expected business loss.

---

# 1. Overall State-Inference Performance

The agent correctly inferred the latent state for:

> **35 / 40 test batches**

giving an overall accuracy of:

> ## **87.5%**

### Overall Metrics

| Metric | Result |
|---|---:|
| **Accuracy** | **87.5%** |
| **Macro Precision** | **88.5%** |
| **Macro Recall** | **85.4%** |
| **Macro F1** | **83.8%** |

These metrics summarize state inference only.

They do not yet measure whether the action selected by the agent was economically sensible.

---

# 2. Performance by Hidden State

| State | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `S1_HEALTHY` | 91.7% | 91.7% | 91.7% | 24 |
| `S2_BENIGN_DRIFT` | **100.0%** | **50.0%** | 66.7% | 6 |
| `S3_FORMAT_GLITCH` | **100.0%** | **100.0%** | **100.0%** | 5 |
| `S4_CORRUPTED` | 62.5% | **100.0%** | 76.9% | 5 |

The strongest performance occurred on `S3_FORMAT_GLITCH`.

All five format-glitch batches were correctly identified.

The system also achieved:

> **100% recall on genuinely corrupted batches.**

All **5 / 5** corrupted batches were identified as `S4_CORRUPTED`.

However, corruption precision was only:

> **62.5%**

This means the agent sometimes predicted corruption when the underlying batch was actually healthy or benign drift.

The weakest state was:

> ## `S2_BENIGN_DRIFT`

Only **3 of 6** benign-drift batches were correctly identified, resulting in:

> **50% recall**

This became the most important state-level weakness uncovered by the experiment.

---

# 3. Confusion Matrix

The complete confusion matrix was:

| True ↓ / Predicted → | Healthy | Benign Drift | Format Glitch | Corrupted |
|---|---:|---:|---:|---:|
| **Healthy** | **22** | 0 | 0 | **2** |
| **Benign Drift** | **2** | **3** | 0 | **1** |
| **Format Glitch** | 0 | 0 | **5** | 0 |
| **Corrupted** | 0 | 0 | 0 | **5** |

The matrix makes the failure pattern clearer.

### Healthy

22 / 24 healthy batches were correctly identified.

The remaining two were incorrectly classified as Corrupted.

### Benign Drift

Only 3 / 6 benign-drift batches were correctly identified.

Of the remaining three:

- 2 were classified as Healthy
- 1 was classified as Corrupted

### Format Glitch

5 / 5 were correctly identified.

### Corrupted

5 / 5 were correctly identified.

Therefore, all five state-inference errors occurred around the boundaries between:

**Healthy ↔ Benign Drift ↔ Corrupted**

rather than Format Glitch.

---

# 4. The Five Incorrect State Inferences

| Batch | Ground Truth | Predicted | Top Posterior | Action | Realized Simulated Cost |
|---|---|---|---:|---|---:|
| **6** | Benign Drift | Healthy | 57.08% | REPAIR | ₹2,500 |
| **24** | Benign Drift | Corrupted | 36.70% | ISOLATE | ₹5,000 |
| **25** | Healthy | Corrupted | 48.24% | ISOLATE | ₹7,000 |
| **32** | Benign Drift | Healthy | 45.73% | REPAIR | ₹2,500 |
| **38** | Healthy | Corrupted | 60.80% | ISOLATE | ₹7,000 |

These five errors are not all caused by the same component.

Examining the complete decision traces reveals three different failure modes.

---

# 5. Failure Mode 1 — Prior Bias Toward Healthy

### Affected batches

- Batch 6
- Batch 32

Both batches have ground truth:

> `S2_BENIGN_DRIFT`

but were ultimately predicted as:

> `S1_HEALTHY`

Interestingly, the LLM itself assigned its **highest likelihood to the correct state** in both cases.

---

## Batch 6

### Evidence

| Signal | Value |
|---|---:|
| Records | 100 |
| Negative amounts | 0 |
| Overflow values | 0 |
| Null receivers | 0 |
| Slash dates | 0 |
| Padded statuses | 0 |
| Lowercase currencies | **65** |
| Median amount | **7063.195** |
| Critical error | False |
| Format error | False |
| Distribution surge | **True** |

The evidence contains substantial distribution and representation change without critical corruption signals.

### LLM likelihoods

| State | `P(Evidence \| State)` |
|---|---:|
| Healthy | 0.25 |
| **Benign Drift** | **0.80** |
| Format Glitch | 0.55 |
| Corrupted | 0.02 |

The LLM correctly considered Benign Drift the most plausible explanation.

However, the experimental prior was:

| State | Prior |
|---|---:|
| Healthy | **0.75** |
| Benign Drift | **0.12** |
| Format Glitch | 0.08 |
| Corrupted | 0.05 |

Before normalization, Bayes therefore produces:

\[
Healthy = 0.75 \times 0.25 = 0.1875
\]

while:

\[
Benign\ Drift = 0.12 \times 0.80 = 0.096
\]

Despite the LLM assigning more than three times the likelihood to Benign Drift, the large Healthy prior dominates.

The resulting posterior becomes:

| State | Posterior |
|---|---:|
| **Healthy** | **57.08%** |
| Benign Drift | 29.22% |
| Format Glitch | 13.39% |
| Corrupted | 0.30% |

The final predicted state is therefore incorrectly:

> `S1_HEALTHY`

---

## Batch 32

The same pattern appears again.

### Evidence

| Signal | Value |
|---|---:|
| Records | 100 |
| Negative amounts | 0 |
| Overflow values | 0 |
| Null receivers | 0 |
| Slash dates | 0 |
| Padded statuses | 0 |
| Lowercase currencies | **49** |
| Median amount | **3518.74** |
| Critical error | False |
| Format error | False |
| Distribution surge | **True** |

### LLM likelihoods

| State | `P(Evidence \| State)` |
|---|---:|
| Healthy | 0.15 |
| **Benign Drift** | **0.80** |
| Format Glitch | 0.45 |
| Corrupted | 0.03 |

Again, the LLM's highest likelihood corresponds to the correct hidden state.

After applying the prior, however:

| State | Posterior |
|---|---:|
| **Healthy** | **45.73%** |
| Benign Drift | 39.02% |
| Format Glitch | 14.63% |
| Corrupted | 0.61% |

Healthy narrowly becomes the most probable state.

---

## What failed?

These two errors should **not primarily be attributed to the LLM**.

The LLM correctly preferred Benign Drift in both cases.

The error appears after incorporating the experimental prior.

The assumed prior:

```text
Healthy        75%
Benign Drift   12%
Format Glitch   8%
Corrupted       5%
```

creates a strong initial bias toward Healthy.

This was deliberately documented as an assumption rather than a measured production distribution.

The experiment demonstrates why that distinction matters.

> **A poorly estimated prior can overpower otherwise useful evidence.**

---

## Improvement

A production system should estimate priors from historical labelled batches rather than manually assigning them.

Future experiments should also perform **prior-sensitivity analysis**.

For example, the same benchmark could be evaluated under:

```text
Current prior
75 / 12 / 8 / 5

Uniform prior
25 / 25 / 25 / 25

Moderate healthy prior
50 / 20 / 15 / 15

Empirical prior
estimated from historical batches
```

This would reveal how much of the system's behaviour comes from the evidence versus the assumed base rates.

---

# 6. Failure Mode 2 — Isolated Critical Signals Were Overweighted

### Affected batches

- Batch 25
- Batch 38

Both batches have ground truth:

> `S1_HEALTHY`

but were predicted as:

> `S4_CORRUPTED`

The traces show a strikingly similar pattern.

---

## Batch 25

### Evidence

```text
100 records

Negative amounts      0
Overflow values       0
Null receivers        1
Slash dates           0
Padded statuses       0
Lowercase currencies  0

Median amount         793.54

Critical error        True
Format error          False
Distribution surge    False
```

The only detected critical anomaly is:

> **1 null receiver among 100 records**

Despite the rest of the batch appearing normal, the LLM estimated:

| State | Likelihood |
|---|---:|
| Healthy | **0.04** |
| Benign Drift | 0.05 |
| Format Glitch | 0.12 |
| **Corrupted** | **0.85** |

After Bayesian updating:

| State | Posterior |
|---|---:|
| Healthy | 34.05% |
| Benign Drift | 6.81% |
| Format Glitch | 10.90% |
| **Corrupted** | **48.24%** |

The agent therefore predicts Corrupted.

---

## Batch 38

Batch 38 shows almost exactly the same pattern.

### Evidence

```text
100 records

Negative amounts      0
Overflow values       0
Null receivers        1
Slash dates           0
Padded statuses       0
Lowercase currencies  0

Median amount         882.59

Critical error        True
Format error          False
Distribution surge    False
```

Again, the only critical signal is one null receiver.

The LLM estimates:

| State | Likelihood |
|---|---:|
| Healthy | **0.02** |
| Benign Drift | 0.05 |
| Format Glitch | 0.08 |
| **Corrupted** | **0.85** |

The resulting posterior is:

| State | Posterior |
|---|---:|
| Healthy | 21.46% |
| Benign Drift | 8.58% |
| Format Glitch | 9.16% |
| **Corrupted** | **60.80%** |

Again:

> `S1_HEALTHY → S4_CORRUPTED`

---

## What failed?

These two cases suggest that the evidence reasoner can overweight the **presence** of a critical signal without sufficiently considering its **prevalence and surrounding context**.

The distinction matters.

There is a large difference between:

```text
1 / 100 null receivers
```

and:

```text
80 / 100 null receivers
```

Yet a boolean feature such as:

```text
has_critical_error = True
```

can make those situations appear superficially similar.

The raw count was also available to the LLM, but the resulting likelihoods suggest that the isolated null was still treated as very strong evidence of corruption.

The surrounding evidence was otherwise healthy:

- no negative values,
- no overflow values,
- no formatting anomalies,
- no currency shift,
- no distribution surge.

---

## Improvement

The reasoning prompt should explicitly instruct the LLM to evaluate:

- anomaly frequency,
- anomaly severity,
- percentage of affected records,
- co-occurring anomalies,
- whether the rest of the batch is internally consistent,
- whether one isolated anomaly is sufficient to justify corruption.

For example:

> When evaluating evidence, consider not only whether an anomaly exists, but also its prevalence, severity, co-occurring signals, and the consistency of the remaining records. Do not treat one isolated anomaly as equivalent to batch-wide corruption.

The evidence representation could also explicitly expose normalized rates:

```text
null_receiver_rate = 0.01
lowercase_currency_rate = 0.00
negative_amount_rate = 0.00
```

rather than relying only on counts and boolean summary flags.

---

# 7. Failure Mode 3 — Drift Requires Operational Context

### Affected batch

- Batch 24

Batch 24 is different from the previous failure modes.

Its evidence genuinely supports multiple competing explanations.

Ground truth:

> `S2_BENIGN_DRIFT`

Initial prediction:

> `S4_CORRUPTED`

---

## Evidence

```text
100 records

57 lowercase currencies
Median amount = 5322.94

1 null receiver

Critical error       = True
Format error         = False
Distribution surge   = True
```

This creates competing interpretations.

### Evidence supporting Benign Drift

- 57 lowercase currency values
- substantial amount-distribution shift
- no negative values
- no overflow values

### Evidence supporting Corruption

- one null receiver
- critical-error flag

The LLM estimated:

| State | Likelihood |
|---|---:|
| Healthy | 0.03 |
| Benign Drift | 0.25 |
| Format Glitch | 0.12 |
| **Corrupted** | **0.72** |

After Bayesian updating:

| State | Posterior |
|---|---:|
| Healthy | 22.94% |
| Benign Drift | 30.58% |
| Format Glitch | 9.79% |
| **Corrupted** | **36.70%** |

Corruption wins, but only narrowly.

The posterior is highly uncertain:

```text
Corrupted       36.70%
Benign Drift    30.58%
Healthy         22.94%
Format Glitch    9.79%
```

---

## Additional Context Experiment

We then deliberately supplied additional contextual evidence:

> A producer deployment earlier today intentionally changed currency codes to lowercase, and the higher transaction amounts are explained by a legitimate promotion. The single null receiver is known to be caused by an optional legacy field.

This clue was **constructed for the experiment** to test sequential belief updating.

It was not obtained from a real production incident.

The LLM estimated:

| State | `P(New Evidence \| State)` |
|---|---:|
| Healthy | 0.40 |
| **Benign Drift** | **0.90** |
| Format Glitch | 0.35 |
| Corrupted | 0.05 |

Using the previous posterior as the new prior produced:

| State | Before | → | After |
|---|---:|:---:|---:|
| Healthy | 22.94% | → | 21.87% |
| **Benign Drift** | **30.58%** | → | **65.59%** |
| Format Glitch | 9.79% | → | 8.17% |
| **Corrupted** | **36.70%** | → | **4.37%** |

The dominant state changes from:

```text
CORRUPTED
36.70%
```

to:

```text
BENIGN DRIFT
65.59%
```

which matches the hidden ground truth.

---

## What failed?

The initial evidence did not contain enough **operational context** to explain why the distribution had changed.

The system could observe:

> "The distribution changed."

But it could not initially know:

> "The distribution changed because of an intentional deployment and legitimate promotion."

This exposes a fundamental limitation of reasoning from batch statistics alone.

Some anomalies cannot be classified correctly without information about the process that generated them.

---

## Improvement

Future evidence sources could include:

- producer deployment history,
- recent schema/configuration changes,
- business-event calendars,
- upstream pipeline status,
- previous batch trends,
- human reviewer input,
- producer explanations,
- downstream validation results.

This finding directly motivates the **new-evidence / feedback loop** in the agent architecture.

The agent should not necessarily make a permanent decision from the first observation.

When uncertainty remains high, it can gather additional evidence and update its existing belief.

---

# 8. Policy Behaviour Under Inference Failure

The system is not designed solely as a state classifier.

After estimating the posterior belief, it independently evaluates the expected loss of each action:

\[
E[\text{Loss}(a)]
=
\sum_s P(s \mid E) \times Cost(a,s)
\]

This separation matters when inference is wrong.

The five incorrect state predictions produced:

| Batch | Inference Error | Final Action | Realized Simulated Cost |
|---|---|---|---:|
| 6 | Drift → Healthy | REPAIR | ₹2,500 |
| 24 | Drift → Corrupted | ISOLATE | ₹5,000 |
| 25 | Healthy → Corrupted | ISOLATE | ₹7,000 |
| 32 | Drift → Healthy | REPAIR | ₹2,500 |
| 38 | Healthy → Corrupted | ISOLATE | ₹7,000 |

Notably, none of these five state-inference errors resulted in a `REJECT` decision.

This is particularly visible in Batches 25 and 38.

Both were incorrectly predicted as corrupted.

A simple classifier-to-action system might use:

```text
Predicted Corrupted
        ↓
      REJECT
```

The expected-loss policy did not do this.

Instead, uncertainty over the remaining states made `ISOLATE` cheaper than `REJECT`.

---

# 9. Decision-Level Performance

Because this is a decision agent, state-inference accuracy is only one evaluation dimension.

The experiment also compared the total simulated business cost of different policies.

| System | Total Simulated Cost |
|---|---:|
| Naive ACCEPT Baseline | **₹5,013,700** |
| Strict Reject Baseline | **₹502,500** |
| **LLM + Bayesian Agent** | **₹68,800** |

The final system achieved:

| Comparison | Reduction |
|---|---:|
| vs Naive ACCEPT | **98.6%** |
| vs Strict Reject | **86.3%** |

This is important because the state classifier was not perfect:

> **State accuracy = 87.5%**

Yet the resulting decision cost was substantially lower than both simple baselines.

This demonstrates the distinction between:

> **Prediction quality**

and

> **Decision quality**

A wrong state prediction does not necessarily imply the worst possible action.

Likewise, maximizing classification accuracy is not automatically equivalent to minimizing business loss.

The objective of the agent is therefore:

> **Make the lowest-expected-cost decision given the current uncertainty.**

---

# 10. Safety-Critical Performance

For the most dangerous state, `S4_CORRUPTED`:

| Metric | Result |
|---|---:|
| Precision | 62.5% |
| **Recall** | **100.0%** |
| F1 | 76.9% |
| Support | 5 |

All five corrupted batches were detected.

```text
True Corrupted Batches:      5
Detected as Corrupted:       5
Missed Corrupted Batches:    0
```

Within this synthetic benchmark, the system therefore had **no false negatives for corruption**.

However, this safety came with false positives:

Healthy and benign-drift batches were sometimes classified as corrupted.

This explains the relatively low corruption precision of 62.5%.

The system therefore currently behaves more conservatively around potential corruption.

Given the small synthetic dataset, these numbers should **not** be interpreted as production safety guarantees.

---

# 11. What We Learned From the Failures

The five failures reveal different weaknesses at different layers of the system.

| Failure | Main Layer | Lesson |
|---|---|---|
| Batch 6 | Prior / Bayes | Healthy prior overpowered correct drift evidence |
| Batch 32 | Prior / Bayes | Healthy prior overpowered correct drift evidence |
| Batch 25 | LLM interpretation | Isolated null was overweighted |
| Batch 38 | LLM interpretation | Isolated null was overweighted |
| Batch 24 | Available evidence | Operational context was missing |

This distinction is useful because it prevents treating every wrong prediction as simply:

> "The LLM was wrong."

Instead, the system can fail because of:

```text
Evidence
   │
   ├── insufficient context
   │
   ▼
LLM Interpretation
   │
   ├── likelihood estimation error
   │
   ▼
Bayesian Update
   │
   ├── incorrect / poorly estimated prior
   │
   ▼
Decision Policy
   │
   ├── incorrect cost assumptions
   │
   ▼
Action
```

Different failure sources require different fixes.

---

# 12. Improvements Identified

The experiment suggests several concrete improvements.

### 1. Learn the prior from historical data

The current:

```text
75% Healthy
12% Benign Drift
 8% Format Glitch
 5% Corrupted
```

distribution is an experimental assumption.

Production priors should be estimated from observed historical frequencies.

---

### 2. Run prior-sensitivity experiments

The same benchmark should be evaluated using different priors to determine how sensitive predictions and decisions are to the assumed base rates.

This is particularly important because Batches 6 and 32 demonstrate that the current prior can change the winning state even when the LLM strongly prefers the correct explanation.

---

### 3. Represent anomaly prevalence explicitly

Instead of only:

```text
c_null_receiver = 1
has_critical_error = True
```

the evidence representation could include:

```text
null_receiver_rate = 1%
```

This makes the difference between isolated and batch-wide failures explicit.

---

### 4. Improve the LLM reasoning instructions

The LLM should explicitly consider:

- prevalence,
- severity,
- co-occurrence,
- surrounding healthy evidence,
- alternative explanations,
- batch size.

This may reduce overreaction to isolated anomalies.

---

### 5. Gather operational context

Distribution changes should be compared against:

- deployments,
- schema changes,
- business events,
- producer behaviour,
- historical batch patterns.

This is especially important for distinguishing Benign Drift from Corruption.

---

### 6. Use sequential evidence gathering

When posterior uncertainty remains high, the agent should be able to obtain additional evidence rather than immediately committing to an irreversible decision.

The Batch 24 experiment demonstrates that new context can substantially revise the posterior.

---

### 7. Calibrate LLM likelihood estimates

The LLM currently generates values interpreted as:

\[
P(Evidence \mid State)
\]

These values have not yet been demonstrated to be statistically calibrated.

A larger labelled benchmark would allow calibration analysis.

---

### 8. Expand the evaluation dataset

The current benchmark contains only:

> **40 synthetic batches**

including:

- 24 Healthy
- 6 Benign Drift
- 5 Format Glitch
- 5 Corrupted

This is sufficient for demonstrating the mechanism but too small for strong generalization claims.

Future evaluation should include more cases, especially ambiguous Benign Drift examples.

---

### 9. Validate the cost matrix

The current rupee costs are simulated assumptions.

Real production costs should ideally be estimated from:

- downstream incident severity,
- reviewer time,
- pipeline downtime,
- repair effort,
- lost transactions,
- false-rejection consequences.

The expected-loss policy is only as meaningful as the costs supplied to it.

---

# 13. Final Takeaway

The experiment achieved:

> **87.5% state-inference accuracy**

with:

> **100% recall on the five corrupted test batches**

and a total simulated decision cost of:

> **₹68,800**

compared with:

> ₹5,013,700 for Naive ACCEPT  
> ₹502,500 for Strict Reject

But the failures are more informative than the headline numbers.

They reveal three concrete weaknesses:

```text
1. PRIOR
   Healthy prior can overpower Benign Drift evidence.

2. INTERPRETATION
   Isolated critical anomalies can be overweighted.

3. EVIDENCE
   Batch statistics alone may not explain legitimate operational drift.
```

They also reveal a useful property of the architecture:

```text
Wrong inference
      │
      ▼
Uncertainty retained
      │
      ▼
Expected-loss policy
      │
      ▼
Cautious action
```

All five state-inference errors resulted in either `REPAIR` or `ISOLATE`, rather than an automatic `REJECT`.

The main lesson is therefore:

> **A useful decision agent should not only ask, "Which state is most likely?"**
>
> **It should ask, "Given what I currently believe and the cost of being wrong, what is the best action to take?"**

The failure analysis also shows where the next iteration should focus: **better priors, prevalence-aware evidence interpretation, richer operational context, calibrated likelihoods, and more evaluation data.**
