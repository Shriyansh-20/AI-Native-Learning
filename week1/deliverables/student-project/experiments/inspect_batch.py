import json
import sys
from pathlib import Path

from src.agent import PaymentTriageAgent, COST_MATRIX


DATASET_PATH = Path("data/test_batches_v2.json")
CACHE_PATH = Path("data/llm_likelihood_cache.json")


def load_batches():
    with DATASET_PATH.open() as f:
        data = json.load(f)

    if isinstance(data, dict) and "batches" in data:
        return data["batches"]

    return data


def load_cache():
    with CACHE_PATH.open() as f:
        return json.load(f)


def main():
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "  python3 -m experiments.inspect_batch <batch_id>"
        )
        sys.exit(1)

    batch_id = str(sys.argv[1])

    batches = load_batches()
    cache = load_cache()

    batch = next(
        (
            b
            for b in batches
            if str(b["batch_id"]) == batch_id
        ),
        None,
    )

    if batch is None:
        raise ValueError(
            f"Batch {batch_id} not found in {DATASET_PATH}"
        )

    if batch_id not in cache:
        raise ValueError(
            f"No cached LLM likelihood found for batch {batch_id}"
        )

    agent = PaymentTriageAgent()

    records = batch["records"]
    true_state = batch["true_state"]

    evidence = agent.extract_evidence(records)

    likelihoods = cache[batch_id]["likelihoods"]

    belief = agent.update_belief(likelihoods)

    predicted_state = max(
        belief,
        key=belief.get,
    )

    action, expected_losses = agent.decide_action(
        belief
    )

    realized_cost = COST_MATRIX[action][true_state]

    print("\n" + "=" * 78)
    print(f"BATCH {batch_id} — DECISION TRACE")
    print("=" * 78)

    print("\nGROUND TRUTH")
    print("-" * 78)
    print(true_state)

    print("\nOBSERVED EVIDENCE")
    print("-" * 78)
    for key, value in evidence.items():
        print(f"{key:<30}: {value}")

    print("\nINITIAL PRIOR P(State)")
    print("-" * 78)
    for state, probability in agent.prior.items():
        print(
            f"{state:<24}: "
            f"{probability:.4f} "
            f"({probability:.2%})"
        )

    print("\nLLM-ESTIMATED LIKELIHOODS P(Evidence | State)")
    print("-" * 78)
    for state, value in likelihoods.items():
        print(
            f"{state:<24}: "
            f"{value:.4f}"
        )

    print("\nPOSTERIOR BELIEF P(State | Evidence)")
    print("-" * 78)
    for state, probability in belief.items():
        print(
            f"{state:<24}: "
            f"{probability:.4f} "
            f"({probability:.2%})"
        )

    print("\nSTATE INFERENCE")
    print("-" * 78)
    print(f"True state      : {true_state}")
    print(f"Predicted state : {predicted_state}")
    print(
        f"Confidence      : "
        f"{belief[predicted_state]:.2%}"
    )

    print("\nEXPECTED LOSS BY ACTION")
    print("-" * 78)

    for candidate_action, loss in expected_losses.items():
        marker = (
            "  <-- SELECTED"
            if candidate_action == action
            else ""
        )

        print(
            f"{candidate_action:<12}: "
            f"₹{loss:,.2f}"
            f"{marker}"
        )

    print("\nFINAL ACTION")
    print("-" * 78)
    print(action)

    print("\nREALIZED SIMULATED COST")
    print("-" * 78)
    print(f"₹{realized_cost:,.2f}")

    print("\nSUMMARY")
    print("-" * 78)

    correctness = (
        "CORRECT"
        if predicted_state == true_state
        else "INCORRECT"
    )

    print(
        f"{true_state} -> "
        f"{predicted_state} "
        f"[{correctness}] "
        f"-> {action} "
        f"-> ₹{realized_cost:,.2f}"
    )

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
