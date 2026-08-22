import re
import numpy as np

STATES = ["S1_HEALTHY", "S2_BENIGN_DRIFT", "S3_FORMAT_GLITCH", "S4_CORRUPTED"]
ACTIONS = ["ACCEPT", "REPAIR", "ISOLATE", "REJECT"]

# Cost Matrix in INR (₹)
COST_MATRIX = {
    "ACCEPT": {
        "S1_HEALTHY": 0,
        "S2_BENIGN_DRIFT": 200,
        "S3_FORMAT_GLITCH": 2500,
        "S4_CORRUPTED": 1000000  # Catastrophic ledger pollution
    },
    "REPAIR": {
        "S1_HEALTHY": 500,        # Unnecessary mutation
        "S2_BENIGN_DRIFT": 1200,   # Misapplied format transform
        "S3_FORMAT_GLITCH": 150,   # Successful deterministic repair
        "S4_CORRUPTED": 500000     # False repair (masking corrupted data)
    },
    "ISOLATE": {
        "S1_HEALTHY": 800,        # Review delay / staging hold
        "S2_BENIGN_DRIFT": 800,
        "S3_FORMAT_GLITCH": 800,
        "S4_CORRUPTED": 1200       # Reviewer time + safe catch
    },
    "REJECT": {
        "S1_HEALTHY": 25000,       # False alarm outage / missed SLA
        "S2_BENIGN_DRIFT": 25000,
        "S3_FORMAT_GLITCH": 10000,
        "S4_CORRUPTED": 500        # Clean circuit-breaker catch
    }
}

class PaymentTriageAgent:
    def __init__(self):
        # Prior baseline from 1,000 historical batches
        self.prior = {
            "S1_HEALTHY": 0.75,
            "S2_BENIGN_DRIFT": 0.12,
            "S3_FORMAT_GLITCH": 0.08,
            "S4_CORRUPTED": 0.05
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
            else:
                c_null_receiver += 1
                
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
            "has_critical_error": (c_negative > 0 or c_overflow > 0 or c_null_receiver > 0),
            "has_format_error": (c_slash_date > 0 or c_padded_status > 0),
            "has_distribution_surge": (median_amount > 2000.0 or c_lower_currency > 0)
        }

    def compute_likelihood(self, evidence: dict, state: str) -> float:
        has_crit = evidence["has_critical_error"]
        has_fmt = evidence["has_format_error"]
        has_surge = evidence["has_distribution_surge"]
        
        if state == "S1_HEALTHY":
            if has_crit: return 0.001
            if has_fmt: return 0.01
            if has_surge: return 0.05
            return 0.94
            
        elif state == "S2_BENIGN_DRIFT":
            if has_crit: return 0.005
            if has_fmt: return 0.05
            if has_surge: return 0.90
            return 0.10
            
        elif state == "S3_FORMAT_GLITCH":
            if has_crit: return 0.02
            if has_fmt: return 0.92
            return 0.08
            
        elif state == "S4_CORRUPTED":
            if has_crit: return 0.98
            if has_fmt: return 0.15
            return 0.05
            
        return 0.01

    def update_belief(self, evidence: dict) -> dict:
        unnorm = {}
        for s in STATES:
            unnorm[s] = self.prior[s] * self.compute_likelihood(evidence, s)
            
        total = sum(unnorm.values()) or 1e-9
        return {s: unnorm[s] / total for s in STATES}

    def decide_action(self, belief: dict) -> tuple:
        expected_losses = {}
        for a in ACTIONS:
            loss = sum(belief[s] * COST_MATRIX[a][s] for s in STATES)
            expected_losses[a] = round(loss, 2)
            
        best_action = min(expected_losses, key=expected_losses.get)
        return best_action, expected_losses

# --- Baselines ---

def baseline_naive_accept(records: list) -> str:
    return "ACCEPT"

def baseline_strict_circuit_breaker(evidence: dict) -> str:
    if evidence["has_critical_error"] or evidence["has_format_error"] or evidence["has_distribution_surge"]:
        return "REJECT"
    return "ACCEPT"