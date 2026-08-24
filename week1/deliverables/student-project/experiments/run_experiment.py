import json
from collections import Counter, defaultdict
from pathlib import Path

from src.agent import (
    PaymentTriageAgent,
    baseline_naive_accept,
    baseline_strict_circuit_breaker,
    COST_MATRIX,
    STATES,
    ACTIONS,
)
from src.llm_inference import estimate_likelihoods_with_llm


DATASET_PATH = Path("data/test_batches_v2.json")
CACHE_PATH = Path("data/llm_likelihood_cache.json")


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}

    with CACHE_PATH.open() as f:
        return json.load(f)


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CACHE_PATH.open("w") as f:
        json.dump(cache, f, indent=2)


def get_llm_likelihoods(batch_id, evidence: dict, cache: dict) -> dict:
    """
    Reuse cached LLM likelihoods when available.

    If the LLM fails to produce a valid answer, retry a few times.
    Successful results are immediately cached.
    """

    key = str(batch_id)

    if key in cache:
        print(f"Using cached LLM result for batch {batch_id}...")
        return cache[key]["likelihoods"]

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:
            print(
                f"Calling LLM for batch {batch_id} "
                f"(attempt {attempt}/{max_attempts})..."
            )

            likelihoods = estimate_likelihoods_with_llm(
                evidence
            )

            cache[key] = {
                "batch_id": batch_id,
                "evidence": evidence,
                "likelihoods": likelihoods,
            }

            save_cache(cache)

            return likelihoods

        except Exception as e:

            print(
                f"LLM call failed for batch {batch_id}: {e}"
            )

            if attempt == max_attempts:
                raise

            print("Retrying...")


def evaluate():
    with DATASET_PATH.open() as f:
        test_cases = json.load(f)

    agent = PaymentTriageAgent()
    cache = load_cache()

    # ------------------------------------------------------------------
    # Cost tracking
    # ------------------------------------------------------------------
    total_cost_naive = 0
    total_cost_strict = 0
    total_cost_llm = 0

    # ------------------------------------------------------------------
    # Action tracking
    # ------------------------------------------------------------------
    naive_action_counts = Counter()
    strict_action_counts = Counter()
    llm_action_counts = Counter()

    # ------------------------------------------------------------------
    # State inference tracking
    # ------------------------------------------------------------------
    true_states = []
    predicted_states = []

    true_state_likelihoods = []
    true_state_posteriors = []

    likelihood_by_true_state = defaultdict(list)
    posterior_by_true_state = defaultdict(list)

    case_results = []

    for case in test_cases:
        batch_id = case["batch_id"]
        true_state = case["true_state"]
        records = case["records"]

        # --------------------------------------------------------------
        # 1. Deterministic evidence extraction
        # --------------------------------------------------------------
        evidence = agent.extract_evidence(records)

        # --------------------------------------------------------------
        # 2. Naive baseline
        # --------------------------------------------------------------
        act_naive = baseline_naive_accept(records)
        total_cost_naive += COST_MATRIX[act_naive][true_state]
        naive_action_counts[act_naive] += 1

        # --------------------------------------------------------------
        # 3. Strict baseline
        # --------------------------------------------------------------
        act_strict = baseline_strict_circuit_breaker(evidence)
        total_cost_strict += COST_MATRIX[act_strict][true_state]
        strict_action_counts[act_strict] += 1

        # --------------------------------------------------------------
        # 4. LLM estimates P(Evidence | State)
        # --------------------------------------------------------------
        likelihoods = get_llm_likelihoods(
            batch_id=batch_id,
            evidence=evidence,
            cache=cache,
        )

        # --------------------------------------------------------------
        # 5. Python performs Bayesian update
        #    posterior ∝ prior × likelihood
        # --------------------------------------------------------------
        belief = agent.update_belief(likelihoods)

        predicted_state = max(
            belief,
            key=belief.get,
        )

        # --------------------------------------------------------------
        # 6. Cost-sensitive policy selects action
        # --------------------------------------------------------------
        act_llm, expected_losses = agent.decide_action(belief)

        total_cost_llm += COST_MATRIX[act_llm][true_state]
        llm_action_counts[act_llm] += 1

        # --------------------------------------------------------------
        # Evaluation bookkeeping
        # --------------------------------------------------------------
        true_states.append(true_state)
        predicted_states.append(predicted_state)

        true_likelihood = likelihoods[true_state]
        true_posterior = belief[true_state]

        true_state_likelihoods.append(true_likelihood)
        true_state_posteriors.append(true_posterior)

        likelihood_by_true_state[true_state].append(
            true_likelihood
        )

        posterior_by_true_state[true_state].append(
            true_posterior
        )

        case_results.append({
            "batch_id": batch_id,
            "true_state": true_state,
            "predicted_state": predicted_state,
            "evidence": evidence,
            "likelihoods": likelihoods,
            "belief": belief,
            "action": act_llm,
            "expected_losses": expected_losses,
            "realized_cost": COST_MATRIX[act_llm][true_state],
            "correct_state_prediction": (
                predicted_state == true_state
            ),
        })

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "=" * 72)
    print(
        f"LLM-ASSISTED BAYESIAN EXPERIMENT "
        f"({len(test_cases)} Test Batches)"
    )
    print("=" * 72)

    # ==================================================================
    # 1. COST
    # ==================================================================
    print("\nDECISION COST")
    print("-" * 72)

    print(
        f"1. Naive Accept Baseline:      "
        f"Total Cost = ₹{total_cost_naive:,.2f}"
    )

    print(
        f"2. Strict Reject Baseline:     "
        f"Total Cost = ₹{total_cost_strict:,.2f}"
    )

    print(
        f"3. LLM + Bayesian Agent:       "
        f"Total Cost = ₹{total_cost_llm:,.2f}"
    )

    if total_cost_naive:
        reduction_vs_naive = (
            1 - total_cost_llm / total_cost_naive
        ) * 100

        print(
            f"   Cost Reduction vs Naive:    "
            f"{reduction_vs_naive:.1f}%"
        )

    if total_cost_strict:
        reduction_vs_strict = (
            1 - total_cost_llm / total_cost_strict
        ) * 100

        print(
            f"   Cost Reduction vs Strict:   "
            f"{reduction_vs_strict:.1f}%"
        )

    # ==================================================================
    # 2. ACTION DISTRIBUTION
    # ==================================================================
    print("\nACTION DISTRIBUTION")
    print("-" * 72)

    print(
        f"{'Action':<12}"
        f"{'Naive':>10}"
        f"{'Strict':>10}"
        f"{'LLM+Bayes':>12}"
    )

    print("-" * 44)

    for action in ACTIONS:
        print(
            f"{action:<12}"
            f"{naive_action_counts[action]:>10}"
            f"{strict_action_counts[action]:>10}"
            f"{llm_action_counts[action]:>12}"
        )

    # ==================================================================
    # 3. STATE INFERENCE METRICS
    # ==================================================================
    print("\nSTATE INFERENCE PERFORMANCE")
    print("-" * 72)

    print(
        f"{'State':<22}"
        f"{'Precision':>12}"
        f"{'Recall':>12}"
        f"{'F1':>12}"
        f"{'Support':>10}"
    )

    print("-" * 72)

    metrics_by_state = {}

    for state in STATES:
        tp = sum(
            1
            for true, pred in zip(
                true_states,
                predicted_states,
            )
            if true == state
            and pred == state
        )

        fp = sum(
            1
            for true, pred in zip(
                true_states,
                predicted_states,
            )
            if true != state
            and pred == state
        )

        fn = sum(
            1
            for true, pred in zip(
                true_states,
                predicted_states,
            )
            if true == state
            and pred != state
        )

        support = sum(
            1
            for true in true_states
            if true == state
        )

        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(
            2 * precision * recall,
            precision + recall,
        )

        metrics_by_state[state] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

        print(
            f"{state:<22}"
            f"{precision:>11.1%}"
            f"{recall:>12.1%}"
            f"{f1:>12.1%}"
            f"{support:>10}"
        )

    correct_predictions = sum(
        1
        for true, pred in zip(
            true_states,
            predicted_states,
        )
        if true == pred
    )

    accuracy = safe_divide(
        correct_predictions,
        len(true_states),
    )

    macro_precision = sum(
        metrics_by_state[state]["precision"]
        for state in STATES
    ) / len(STATES)

    macro_recall = sum(
        metrics_by_state[state]["recall"]
        for state in STATES
    ) / len(STATES)

    macro_f1 = sum(
        metrics_by_state[state]["f1"]
        for state in STATES
    ) / len(STATES)

    print("-" * 72)

    print(
        f"{'Overall Accuracy':<22}"
        f"{accuracy:>11.1%}"
    )

    print(
        f"{'Macro Average':<22}"
        f"{macro_precision:>11.1%}"
        f"{macro_recall:>12.1%}"
        f"{macro_f1:>12.1%}"
    )

    # ==================================================================
    # 4. CORRUPTION SAFETY
    # ==================================================================
    corrupted_state = "S4_CORRUPTED"
    corrupted_metrics = metrics_by_state[corrupted_state]

    print("\nCORRUPTION SAFETY")
    print("-" * 72)

    print(
        f"Corrupted Precision: "
        f"{corrupted_metrics['precision']:.1%}"
    )

    print(
        f"Corrupted Recall:    "
        f"{corrupted_metrics['recall']:.1%}"
    )

    print(
        f"Corrupted F1:        "
        f"{corrupted_metrics['f1']:.1%}"
    )

    # ==================================================================
    # 5. PROBABILISTIC DIAGNOSTICS
    # ==================================================================
    avg_true_likelihood = safe_divide(
        sum(true_state_likelihoods),
        len(true_state_likelihoods),
    )

    avg_true_posterior = safe_divide(
        sum(true_state_posteriors),
        len(true_state_posteriors),
    )

    print("\nPROBABILISTIC DIAGNOSTICS")
    print("-" * 72)

    print(
        "Avg LLM-estimated likelihood for true state "
        f"P(E | true state): {avg_true_likelihood:.4f}"
    )

    print(
        "Avg Bayesian posterior for true state        "
        f"P(true state | E): {avg_true_posterior:.1%}"
    )

    print(
        "\nPer-state average likelihood/posterior "
        "for the true state:"
    )

    print(
        f"{'State':<22}"
        f"{'Avg Likelihood':>18}"
        f"{'Avg Posterior':>18}"
    )

    print("-" * 58)

    for state in STATES:
        avg_likelihood = safe_divide(
            sum(likelihood_by_true_state[state]),
            len(likelihood_by_true_state[state]),
        )

        avg_posterior = safe_divide(
            sum(posterior_by_true_state[state]),
            len(posterior_by_true_state[state]),
        )

        print(
            f"{state:<22}"
            f"{avg_likelihood:>18.4f}"
            f"{avg_posterior:>17.1%}"
        )

    # ==================================================================
    # 6. CONFUSION MATRIX
    # ==================================================================
    print("\nCONFUSION MATRIX")
    print("-" * 72)

    print(
        "Rows = true state, "
        "Columns = predicted state"
    )

    short_names = {
        "S1_HEALTHY": "S1",
        "S2_BENIGN_DRIFT": "S2",
        "S3_FORMAT_GLITCH": "S3",
        "S4_CORRUPTED": "S4",
    }

    print(
        f"{'':<22}"
        + "".join(
            f"{short_names[state]:>8}"
            for state in STATES
        )
    )

    for true_state in STATES:
        row = []

        for predicted_state in STATES:
            count = sum(
                1
                for true, pred in zip(
                    true_states,
                    predicted_states,
                )
                if true == true_state
                and pred == predicted_state
            )

            row.append(count)

        print(
            f"{short_names[true_state] + ' ' + true_state:<22}"
            + "".join(
                f"{count:>8}"
                for count in row
            )
        )

    # ==================================================================
    # 7. TOP FAILURES
    # ==================================================================
    failures = [
        result
        for result in case_results
        if not result["correct_state_prediction"]
    ]

    failures.sort(
        key=lambda result: result["realized_cost"],
        reverse=True,
    )

    print("\nTOP INCORRECT STATE INFERENCES")
    print("-" * 72)

    if not failures:
        print("No incorrect state predictions.")
    else:
        for result in failures[:5]:
            confidence = max(
                result["belief"].values()
            )

            print(
                f"Batch {result['batch_id']:>2}: "
                f"true={result['true_state']:<18} "
                f"pred={result['predicted_state']:<18} "
                f"confidence={confidence:.1%} "
                f"action={result['action']:<8} "
                f"cost=₹{result['realized_cost']:,.0f}"
            )

    # ==================================================================
    # 8. CACHE INFO
    # ==================================================================
    print("\nLLM CACHE")
    print("-" * 72)

    print(
        f"Cached likelihood records: "
        f"{len(cache)}/{len(test_cases)}"
    )

    print(
        f"Cache file: {CACHE_PATH}"
    )

    print("=" * 72)


if __name__ == "__main__":
    evaluate()
