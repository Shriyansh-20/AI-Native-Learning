# Failure Analysis

## 1. Overall Evaluation

The final LLM + Bayesian agent was evaluated on **40 synthetic test batches** spanning four latent data-quality states.

### Overall State-Inference Performance

| Metric | Result |
|---|---:|
| **Accuracy** | **87.5%** |
| **Macro Precision** | **88.5%** |
| **Macro Recall** | **85.4%** |
| **Macro F1** | **83.8%** |

The agent correctly inferred the latent state for:

**35 / 40 batches**

Five batches were incorrectly classified.

---

## 2. Performance by State

| State | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `S1_HEALTHY` | 91.7% | 91.7% | 91.7% | 24 |
| `S2_BENIGN_DRIFT` | 100.0% | **50.0%** | 66.7% | 6 |
| `S3_FORMAT_GLITCH` | 100.0% | **100.0%** | 100.0% | 5 |
| `S4_CORRUPTED` | 62.5% | **100.0%** | 76.9% | 5 |

### Safety-Critical Result

For corrupted batches:

- **Recall: 100%**
- Precision: 62.5%
- F1: 76.9%

All **5 / 5 genuinely corrupted batches were identified as corrupted**.

However, corruption precision was only **62.5%**, meaning some non-corrupted batches were incorrectly classified as corrupted.

This is visible in the failure cases below.

---

## 3. Where Did the Errors Occur?

The confusion matrix was:

| True ↓ / Predicted → | Healthy | Drift | Format | Corrupted |
|---|---:|---:|---:|---:|
| **Healthy** | 22 | 0 | 0 | **2** |
| **Benign Drift** | **2** | 3 | 0 | **1** |
| **Format Glitch** | 0 | 0 | 5 | 0 |
| **Corrupted** | 0 | 0 | 0 | 5 |

This immediately reveals the main weakness:

> **Benign Drift was the hardest state for the system to recognize.**

Only **3 of 6 benign-drift batches** were correctly identified, giving it **50% recall**.

By contrast:

- Healthy: 22/24 correctly identified
- Format Glitch: 5/5
- Corrupted: 5/5

The five incorrect state inferences were:

| Batch | Ground Truth | Predicted | Confidence | Action | Realized Simulated Cost |
|---|---|---|---:|---|---:|
| 6 | Benign Drift | Healthy | 57.08% | REPAIR | ₹2,500 |
| 24 | Benign Drift | Corrupted | 36.70% | ISOLATE | ₹5,000 |
| 25 | Healthy | Corrupted | 48.24% | ISOLATE | ₹7,000 |
| 32 | Benign Drift | Healthy | 45.73% | REPAIR | ₹2,500 |
| 38 | Healthy | Corrupted | 60.80% | ISOLATE | ₹7,000 |

These five errors fall into three recurring failure modes.
