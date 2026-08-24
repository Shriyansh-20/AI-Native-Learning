# Probability & Decision Record

This document shows how the Data Quality Triage Agent represents uncertainty, updates its beliefs, and converts those beliefs into actions.

The agent reasons over four possible hidden states:

| State | Meaning |
|---|---|
| `S1_HEALTHY` | Data is fundamentally valid |
| `S2_BENIGN_DRIFT` | Legitimate distribution or representation change |
| `S3_FORMAT_GLITCH` | Recoverable formatting problem |
| `S4_CORRUPTED` | Unsafe semantic/data corruption |

It can take four actions:

`ACCEPT` · `REPAIR` · `ISOLATE` · `REJECT`

The decision pipeline is:

```text
Evidence
   ↓
LLM estimates P(Evidence | State)
   ↓
Bayesian update
   ↓
Posterior belief P(State | Evidence)
   ↓
Expected loss of each action
   ↓
ACCEPT / REPAIR / ISOLATE / REJECT
```

> **Important:** The LLM interprets the evidence. It does not choose the final action. Bayesian inference updates the belief, and the deterministic cost-sensitive policy chooses the action.

---

## Experimental Prior

The current experiment begins with:

| State | Prior |
|---|---:|
| `S1_HEALTHY` | 75% |
| `S2_BENIGN_DRIFT` | 12% |
| `S3_FORMAT_GLITCH` | 8% |
| `S4_CORRUPTED` | 5% |

These are **experimental modelling assumptions**, not empirically measured production base rates.

The assumption is simply that healthy batches are more common than drift, formatting problems, or severe corruption.

For a production system, these priors should instead be estimated and periodically recalibrated from historical labelled batches.

---

# Decision Trace 1 — Clear Healthy Batch

## Batch 1

**Ground truth:** `S1_HEALTHY`  
**Final action:** `ACCEPT` ✅  
**Realized simulated cost:** **₹0**

### 1. What did we observe?

| Signal | Observation |
|---|---:|
| Records | 100 |
| Negative amounts | 0 |
| Overflow values | 0 |
| Null receivers | 0 |
| Slash dates | 0 |
| Padded statuses | 0 |
| Lowercase currencies | 0 |
| Median amount | ₹758.80 |
| Critical error | No |
| Format error | No |
| Distribution surge | No |

No suspicious signal was detected.

### 2. What did the LLM infer?

The LLM estimates likelihoods:

| Possible State | `P(Evidence \| State)` |
|---|---:|
| `S1_HEALTHY` | **0.92** |
| `S2_BENIGN_DRIFT` | 0.15 |
| `S3_FORMAT_GLITCH` | 0.05 |
| `S4_CORRUPTED` | 0.02 |

These are **not yet the posterior probabilities of the states**.

They represent how plausible the observed evidence would be if each state were true.

### 3. How did the belief change?

Bayes combines the likelihoods with the prior:

\[
P(S \mid E)
=
\frac{P(E \mid S)P(S)}
{\sum_j P(E \mid S_j)P(S_j)}
\]

Result:

| State | Prior | → | Posterior |
|---|---:|:---:|---:|
| `S1_HEALTHY` | 75% | → | **96.77%** |
| `S2_BENIGN_DRIFT` | 12% | → | 2.52% |
| `S3_FORMAT_GLITCH` | 8% | → | 0.56% |
| `S4_CORRUPTED` | 5% | → | 0.14% |

The predicted state is:

> **`S1_HEALTHY` — 96.77%**

### 4. What should the agent do?

The agent does not simply map `HEALTHY → ACCEPT`.

For every action it calculates:

\[
E[\text{Loss}(a)]
=
\sum_s P(s \mid E) \times Cost(a,s)
\]

| Action | Expected Loss |
|---|---:|
| **ACCEPT** | **₹1,421.60 ←** |
| REPAIR | ₹3,388.22 |
| ISOLATE | ₹6,924.96 |
| REJECT | ₹24,881.49 |

### Decision

> ## ACCEPT

The evidence strongly supports a healthy batch and `ACCEPT` has the minimum expected loss.

Since the true state was also `S1_HEALTHY`, the realized simulated cost was:

> **₹0**

---

# Decision Trace 2 — An Ambiguous Failure

## Batch 24

This case is more interesting because the evidence is ambiguous and the agent's most likely inferred state is incorrect.

**Ground truth:** `S2_BENIGN_DRIFT`  
**Initial predicted state:** `S4_CORRUPTED` ❌  
**Selected action:** `ISOLATE`  
**Realized simulated cost:** **₹5,000**

### 1. What did we observe?

```text
100 records

57 lowercase currencies      ← distribution / representation change
Median amount ₹5,322.94      ← substantial distribution shift

1 null receiver              ← potentially dangerous

0 negative amounts
0 overflow values
0 format errors
```

The evidence does not point cleanly toward one explanation.

A large number of lowercase currencies and the amount shift are compatible with benign drift.

However, the null receiver produces a critical-error signal and introduces evidence consistent with corruption.

### 2. What did the LLM infer?

| Possible State | `P(Evidence \| State)` |
|---|---:|
| `S1_HEALTHY` | 0.03 |
| `S2_BENIGN_DRIFT` | 0.25 |
| `S3_FORMAT_GLITCH` | 0.12 |
| `S4_CORRUPTED` | **0.72** |

The LLM therefore considered the observed evidence most compatible with corruption.

But:

> **0.72 does not mean there is a 72% posterior probability that the batch is corrupted.**

The prior still has to be incorporated.

### 3. Bayesian belief

| State | Prior | Likelihood | Posterior |
|---|---:|---:|---:|
| `S1_HEALTHY` | 75% | 0.03 | 22.94% |
| `S2_BENIGN_DRIFT` | 12% | 0.25 | 30.58% |
| `S3_FORMAT_GLITCH` | 8% | 0.12 | 9.79% |
| `S4_CORRUPTED` | 5% | 0.72 | **36.70%** |

The most probable state becomes:

> **`S4_CORRUPTED` — 36.70%**

However, the posterior is highly uncertain:

```text
Corrupted        36.70%
Benign Drift     30.58%
Healthy          22.94%
Format Glitch     9.79%
```

No state has even 50% posterior probability.

The state prediction is also wrong because the hidden ground truth is actually:

> `S2_BENIGN_DRIFT`

---

## 4. A Wrong Prediction Does Not Automatically Mean REJECT

A simple classifier might behave like:

```text
Predicted CORRUPTED
        ↓
      REJECT
```

Our agent instead evaluates the consequences of **all four actions across all four possible states**.

| Action | Expected Loss |
|---|---:|
| ACCEPT | ₹367,278.29 |
| REPAIR | ₹111,563.91 |
| **ISOLATE** | **₹4,076.45 ←** |
| REJECT | ₹14,541.28 |

### Decision

> ## ISOLATE

Although corruption is the most probable individual state, the agent remains uncertain.

Rejecting the batch would be expensive if the batch were actually healthy or benign drift.

`ISOLATE` therefore has the lowest expected loss across the complete posterior distribution.

---

## 5. What actually happened?

Ground truth:

> **`S2_BENIGN_DRIFT`**

Prediction:

> **`S4_CORRUPTED` ❌**

Action:

> **`ISOLATE`**

Realized simulated cost:

> **₹5,000**

So:

```text
State inference
      │
      └── WRONG ❌
          Corrupted instead of Benign Drift

                     ↓

Uncertainty representation
      │
      └── USEFUL ✓
          36.7% Corrupted vs 30.6% Drift

                     ↓

Cost-sensitive policy
      │
      └── CAUTIOUS ✓
          ISOLATE instead of REJECT

                     ↓

Realized simulated cost
              ₹5,000
```

This is an example of:

> **Inference failure with policy containment.**

The probabilistic inference layer made the wrong top-state prediction, but the cost-sensitive policy limited the consequence of that error by selecting a cautious, reversible action.

---

# New Evidence Arrives

One advantage of maintaining a probability distribution is that the agent can revise its beliefs when additional information becomes available.

For Batch 24, the current belief is:

```text
Healthy          22.94%
Benign Drift     30.58%
Format Glitch     9.79%
Corrupted        36.70%
```

We then introduce additional contextual evidence:

> A producer deployment earlier today intentionally changed currency codes to lowercase, and the higher transaction amounts are explained by a legitimate promotion. The single null receiver is known to be caused by an optional legacy field.

This clue was deliberately constructed as part of the experiment to test sequential belief updating.

It is **not evidence obtained from a real production incident**.

---

## How does the LLM interpret the new clue?

The LLM estimates:

| State | `P(New Evidence \| State)` |
|---|---:|
| `S1_HEALTHY` | 0.40 |
| `S2_BENIGN_DRIFT` | **0.90** |
| `S3_FORMAT_GLITCH` | 0.35 |
| `S4_CORRUPTED` | 0.05 |

The new context is therefore much more compatible with benign drift than corruption.

---

# Update the Existing Belief

We do not return to the original prior.

The previous posterior becomes the starting belief for the next Bayesian update:

\[
P_{new}(S)
\propto
P(E_{new}\mid S)
\times
P_{old}(S)
\]

The result is:

| State | Before | → | After |
|---|---:|:---:|---:|
| `S1_HEALTHY` | 22.94% | → | 21.87% |
| **`S2_BENIGN_DRIFT`** | **30.58%** | → | **65.59% ↑** |
| `S3_FORMAT_GLITCH` | 9.79% | → | 8.17% |
| **`S4_CORRUPTED`** | **36.70%** | → | **4.37% ↓** |

The new evidence causes a substantial belief revision:

```text
CORRUPTED

36.70%
   │
   │ new contextual evidence
   ▼
 4.37%


BENIGN DRIFT

30.58%
   │
   │ new contextual evidence
   ▼
65.59%
```

The most probable state changes from:

> `S4_CORRUPTED` ❌

to:

> **`S2_BENIGN_DRIFT` ✅**

The revised belief now agrees with the hidden ground truth.

---

# Does the Action Change?

Expected losses are calculated again using the updated posterior:

| Action | Before Evidence | After Evidence |
|---|---:|---:|
| ACCEPT | ₹367,278.29 | ₹44,067.99 |
| REPAIR | ₹111,563.91 | ₹15,431.98 |
| **ISOLATE** | **₹4,076.45** | **₹5,202.65** |
| REJECT | ₹14,541.28 | ₹22,703.62 |

Interestingly:

> **The belief changes dramatically, but the action does not.**

The agent still chooses:

> ## ISOLATE

---

## Why?

After the new evidence, the probability of corruption is only:

**4.37%**

But in our experimental cost matrix, accepting a genuinely corrupted batch costs:

**₹1,000,000**

Therefore, the corruption component alone contributes approximately:

\[
0.0437 \times ₹1,000,000
\approx ₹43,700
\]

to the expected loss of `ACCEPT`.

That explains most of its total:

**₹44,067.99**

Likewise, repairing a corrupted batch carries an assumed cost of ₹300,000, keeping `REPAIR` more expensive than `ISOLATE`.

Therefore:

> **A large change in belief does not necessarily require a change in action.**

The final decision depends on both:

**Probability × Consequence**

---

# What Do These Two Batches Demonstrate?

| | Batch 1 | Batch 24 |
|---|---|---|
| Scenario | Clear | Ambiguous |
| Ground truth | Healthy | Benign Drift |
| Initial prediction | Healthy ✅ | Corrupted ❌ |
| Highest posterior | 96.77% | 36.70% |
| Initial action | ACCEPT | ISOLATE |
| State inference correct? | ✅ | ❌ |
| Policy behaviour | Confident acceptance | Cautious containment |
| New evidence tested? | — | ✅ |
| Belief revised? | — | Yes |
| Corruption belief | 0.14% | 36.70% → 4.37% |
| Drift belief | 2.52% | 30.58% → 65.59% |
| Action changed? | — | No |

The cases demonstrate two different behaviours.

### When evidence is clear

The agent can become highly confident and take the inexpensive action.

**Batch 1:**

`Healthy → 96.77% → ACCEPT → ₹0`

### When evidence is ambiguous

The agent can preserve uncertainty instead of forcing a confident classification.

**Batch 24:**

`Ambiguous Evidence → uncertain belief → ISOLATE`

When new information arrives:

`New Evidence → revised belief → recompute decision`

---

# Experimental Assumptions & Limitations

These results should be interpreted within the scope of the experiment.

### Prior probabilities are assumed

The `75% / 12% / 8% / 5%` initial prior is an experimental modelling assumption.

It is not an empirically measured production base rate.

### LLM likelihoods are estimates

The values produced as `P(Evidence | State)` are LLM-generated estimates.

They have **not yet been demonstrated to be statistically calibrated likelihoods**.

A larger labelled evaluation would be needed to test calibration.

### Costs are simulated

The rupee values in the cost matrix represent assumed relative business consequences.

They are used to compare policies and are **not measured financial losses**.

### The evaluation dataset is synthetic

The benchmark contains 40 synthetic payment batches designed to exercise different latent states and overlapping evidence patterns.

Results therefore demonstrate behaviour within this experimental environment rather than production-level generalization.

### The additional Batch 24 clue is simulated

The contextual clue used for the sequential update was deliberately constructed to test whether the agent could update an existing belief when new evidence arrived.

It was not obtained from a real producer incident.

---

# Core Takeaway

The agent deliberately separates three different responsibilities:

```text
                 LLM
Evidence ─────────────────→ Likelihood
                                │
                                ▼
                              Bayes
                                │
                                ▼
                              Belief
                                │
                                ▼
                         Expected-Loss
                             Policy
                                │
                                ▼
                              Action
```

### The LLM interprets.

It estimates:

\[
P(Evidence \mid State)
\]

### Bayes updates.

It calculates:

\[
P(State \mid Evidence)
\]

### The policy decides.

It minimizes:

\[
E[\text{Loss}(Action)]
\]

This separation allows us to inspect not only **what the agent did**, but also:

- what it believed,
- how uncertain it was,
- why its belief changed,
- where its inference failed,
- how the policy responded to that failure,
- and why the final action was selected.

Batch 24 is particularly useful because the initial inference was wrong, but the uncertainty-aware decision policy contained the error and subsequent evidence moved the belief toward the correct latent state.
