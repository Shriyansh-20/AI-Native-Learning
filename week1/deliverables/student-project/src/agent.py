import re
import numpy as np

STATES = ["S1_HEALTHY", "S2_BENIGN_DRIFT", "S3_FORMAT_GLITCH", "S4_CORRUPTED"]
ACTIONS = ["ACCEPT", "REPAIR", "ISOLATE", "REJECT"]

# Cost Matrix in INR (₹)
#
# Design goal:
# - ACCEPT should be best for very likely healthy batches.
# - REPAIR should be attractive for likely format glitches.
# - REJECT should be attractive for highly likely corruption.
# - ISOLATE should remain a safe fallback, but should NOT dominate every belief.
#
# These are experimental costs for the Week-1 simulator. They should be
# documented as assumptions rather than treated as measured production costs.
COST_MATRIX = {
    "ACCEPT": {
        "S1_HEALTHY": 0,
        "S2_BENIGN_DRIFT": 200,
        "S3_FORMAT_GLITCH": 2500,
        "S4_CORRUPTED": 1000000,
    },
    "REPAIR": {
        "S1_HEALTHY": 3000,
        "S2_BENIGN_DRIFT": 2500,
        "S3_FORMAT_GLITCH": 200,
        "S4_CORRUPTED": 300000,
    },
    "ISOLATE": {
        "S1_HEALTHY": 7000,
        "S2_BENIGN_DRIFT": 5000,
        "S3_FORMAT_GLITCH": 4000,
        "S4_CORRUPTED": 1500,
    },
    "REJECT": {
        "S1_HEALTHY": 25000,
        "S2_BENIGN_DRIFT": 25000,
        "S3_FORMAT_GLITCH": 10000,
        "S4_CORRUPTED": 500,
    },
}


class PaymentTriageAgent:
    def __init__(self):
        # Prior baseline from historical/simulated batches.
        # For Week 1 these are explicit assumptions.
        self.prior = {
            "S1_HEALTHY": 0.75,
            "S2_BENIGN_DRIFT": 0.12,
            "S3_FORMAT_GLITCH": 0.08,
            "S4_CORRUPTED": 0.05,
        }

    def extract_evidence(self, batch_records: list) -> dict:
        n = len(batch_records)

        c_negative = 0
        c_overflow = 0
        c_null_receiver = 0
        c_slash_date = 0
        c_padded_status = 0
        c_lower_currency = 0
        amounts = []

        for r in batch_records:
            amt = r.get("amount")

            if amt is not None:
                amounts.append(amt)

                if amt < 0:
                    c_negative += 1
                elif amt > 500000:
                    c_overflow += 1

            if r.get("receiver_account") is None:
                c_null_receiver += 1

            ts = str(r.get("timestamp", ""))
            if re.match(r"^\d{2}/\d{2}/\d{4}", ts):
                c_slash_date += 1

            st = str(r.get("status", ""))
            if st != st.strip():
                c_padded_status += 1

            cur = str(r.get("currency", ""))
            if cur.islower():
                c_lower_currency += 1

        median_amount = float(np.median(amounts)) if amounts else 0.0

        return {
            "num_records": n,
            "c_negative": c_negative,
            "c_overflow": c_overflow,
            "c_null_receiver": c_null_receiver,
            "c_slash_date": c_slash_date,
            "c_padded_status": c_padded_status,
            "c_lower_currency": c_lower_currency,
            "median_amount": median_amount,
            "has_critical_error": (
                c_negative > 0
                or c_overflow > 0
                or c_null_receiver > 0
            ),
            "has_format_error": (
                c_slash_date > 0
                or c_padded_status > 0
            ),
            "has_distribution_surge": (
                median_amount > 2000.0
                or c_lower_currency > 0
            ),
        }

    # def compute_likelihood(self, evidence: dict, state: str) -> float:
    #     """
    #     Handcrafted Week-1 inference baseline.

    #     These values intentionally remain as the rule-based comparison system.
    #     Later, an LLM inference module can replace update_belief() while the same
    #     decide_action() policy is reused.
    #     """
    #     has_crit = evidence["has_critical_error"]
    #     has_fmt = evidence["has_format_error"]
    #     has_surge = evidence["has_distribution_surge"]

    #     if state == "S1_HEALTHY":
    #         if has_crit:
    #             return 0.001
    #         if has_fmt:
    #             return 0.01
    #         if has_surge:
    #             return 0.05
    #         return 0.94

    #     if state == "S2_BENIGN_DRIFT":
    #         if has_crit:
    #             return 0.005
    #         if has_fmt:
    #             return 0.05
    #         if has_surge:
    #             return 0.90
    #         return 0.10

    #     if state == "S3_FORMAT_GLITCH":
    #         if has_crit:
    #             return 0.02
    #         if has_fmt:
    #             return 0.92
    #         return 0.08

    #     if state == "S4_CORRUPTED":
    #         if has_crit:
    #             return 0.98
    #         if has_fmt:
    #             return 0.15
    #         return 0.05

    #     return 0.01

    def update_belief(self, likelihoods: dict) -> dict:
        """
        Bayesian update:

        posterior ∝ prior × likelihood

        likelihoods[state] represents:
            P(Evidence | State)
        """

        unnorm = {}

        for state in STATES:
            if state not in likelihoods:
                raise ValueError(
                    f"Missing likelihood for {state}"
                )

            unnorm[state] = (
                self.prior[state]
                * likelihoods[state]
            )

        total = sum(unnorm.values())

        if total <= 0:
            raise ValueError(
                "Likelihoods produced zero total probability."
            )

        return {
            state: unnorm[state] / total
            for state in STATES
        }

    def decide_action(self, belief: dict) -> tuple:
        expected_losses = {}

        for action in ACTIONS:
            expected_loss = sum(
                belief[state] * COST_MATRIX[action][state]
                for state in STATES
            )
            expected_losses[action] = round(expected_loss, 2)

        best_action = min(
            expected_losses,
            key=expected_losses.get,
        )

        return best_action, expected_losses


# ----------------------------------------------------------------------
# Baselines
# ----------------------------------------------------------------------

def baseline_naive_accept(records: list) -> str:
    return "ACCEPT"


def baseline_strict_circuit_breaker(evidence: dict) -> str:
    if (
        evidence["has_critical_error"]
        or evidence["has_format_error"]
        or evidence["has_distribution_surge"]
    ):
        return "REJECT"

    return "ACCEPT"
