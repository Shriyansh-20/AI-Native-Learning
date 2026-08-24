import json
from pathlib import Path

from src.agent import PaymentTriageAgent, STATES
from src.llm_inference import estimate_likelihoods_with_llm


BATCH_ID = "24"

DATASET_PATH = Path("data/test_batches_v2.json")
CACHE_PATH = Path("data/llm_likelihood_cache.json")


# Additional contextual evidence used for the sequential-update demonstration.
NEW_EVIDENCE = """
A producer deployment earlier today intentionally changed currency codes
to lowercase, and the higher transaction amounts are explained by a
legitimate promotion. The single null receiver is known to be caused by
an optional legacy field.
""".strip()


def normalize_update(prior, likelihoods):
    """
    Bayesian update:
        posterior(S) ∝ likelihood(E | S) * prior(S)
    """
    unnormalized = {
        state: prior[state] * likelihoods[state]
        for state in STATES
    }

    total = sum(unnormalized.values())

    if total <= 0:
        raise ValueError("Likelihoods produced zero total probability.")

    return {
        state: unnormalized[state] / total
        for state in STATES
    }


def main():
    # ------------------------------------------------------------
    # 1. Load Batch 24
    # ------------------------------------------------------------

    with DATASET_PATH.open() as f:
        batches = json.load(f)

    if isinstance(batches, dict) and "batches" in batches:
        batches = batches["batches"]

    batch = next(
        b for b in batches
        if str(b["batch_id"]) == BATCH_ID
    )

    # ------------------------------------------------------------
    # 2. Reconstruct the original belief using the cached
    #    likelihood generated during the 40-batch experiment.
    # ------------------------------------------------------------

    agent = PaymentTriageAgent()

    evidence = agent.extract_evidence(batch["records"])

    with CACHE_PATH.open() as f:
        cache = json.load(f)

    original_likelihoods = cache[BATCH_ID]["likelihoods"]

    previous_belief = agent.update_belief(original_likelihoods)

    original_action, original_losses = agent.decide_action(
        previous_belief
    )

    # ------------------------------------------------------------
    # 3. Ask the LLM to interpret the NEW contextual evidence.
    #
    #    This is a separate observation E2.
    # ------------------------------------------------------------

    new_evidence_for_llm = {
        "previous_batch_evidence": evidence,
        "additional_context": NEW_EVIDENCE,
    }

    new_likelihoods = None

    for attempt in range(1, 4):
        try:
            print(
                f"Calling LLM for new evidence "
                f"(attempt {attempt}/3)..."
            )

            new_likelihoods = estimate_likelihoods_with_llm(
                new_evidence_for_llm
            )

            break

        except Exception as exc:
            print(f"LLM call failed: {exc}")

            if attempt == 3:
                raise

            print("Retrying...")

    if new_likelihoods is None:
        raise RuntimeError(
            "Failed to obtain likelihoods for new evidence."
        )

    # ------------------------------------------------------------
    # 4. Sequential Bayesian update.
    #
    #    IMPORTANT:
    #    previous posterior P(S | E1) becomes the prior
    #    for the new observation E2.
    #
    #    P(S | E1, E2)
    #        ∝ P(E2 | S) * P(S | E1)
    # ------------------------------------------------------------

    updated_belief = normalize_update(
        previous_belief,
        new_likelihoods,
    )

    # ------------------------------------------------------------
    # 5. Recompute expected losses using the updated belief.
    # ------------------------------------------------------------

    updated_action, updated_losses = agent.decide_action(
        updated_belief
    )

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("BATCH 24 — BELIEF UPDATE AFTER NEW EVIDENCE")
    print("=" * 70)

    print("\nGROUND TRUTH")
    print(batch["true_state"])

    print("\nPREVIOUS BELIEF")
    for state in STATES:
        print(
            f"{state:<24}: "
            f"{previous_belief[state]:.2%}"
        )

    print("\nPREVIOUS ACTION")
    print(original_action)

    print("\nNEW EVIDENCE")
    print(NEW_EVIDENCE)

    print("\nLLM-ESTIMATED LIKELIHOODS FOR NEW EVIDENCE")
    for state in STATES:
        print(
            f"{state:<24}: "
            f"{new_likelihoods[state]:.4f}"
        )

    print("\nUPDATED POSTERIOR BELIEF")
    for state in STATES:
        print(
            f"{state:<24}: "
            f"{updated_belief[state]:.2%}"
        )

    print("\nEXPECTED LOSS AFTER NEW EVIDENCE")
    for action, loss in updated_losses.items():
        print(
            f"{action:<10}: "
            f"₹{loss:,.2f}"
        )

    print("\nUPDATED ACTION")
    print(updated_action)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
