import json
from collections import defaultdict
from src.agent import PaymentTriageAgent, baseline_naive_accept, baseline_strict_circuit_breaker, COST_MATRIX, STATES

def evaluate():
    with open("data/test_batches.json") as f:
        test_cases = json.load(f)
        
    agent = PaymentTriageAgent()
    
    total_cost_naive = 0
    total_cost_strict = 0
    total_cost_bayes = 0
    
    for case in test_cases:
        true_state = case["true_state"]
        records = case["records"]
        
        evidence = agent.extract_evidence(records)
        
        # Policy 1: Naive Accept
        act_naive = baseline_naive_accept(records)
        total_cost_naive += COST_MATRIX[act_naive][true_state]
        
        # Policy 2: Strict Circuit Breaker
        act_strict = baseline_strict_circuit_breaker(evidence)
        total_cost_strict += COST_MATRIX[act_strict][true_state]
        
        # Policy 3: Bayesian Agent
        belief = agent.update_belief(evidence)
        act_bayes, _ = agent.decide_action(belief)
        total_cost_bayes += COST_MATRIX[act_bayes][true_state]
        
    print("=" * 60)
    print("EXPERIMENT BENCHMARK SUMMARY (40 Test Batches)")
    print("=" * 60)
    print(f"1. Naive Accept Baseline:     Total Cost = ₹{total_cost_naive:,.2f}")
    print(f"2. Strict Reject Baseline:    Total Cost = ₹{total_cost_strict:,.2f}")
    print(f"3. Bayesian Agent (V5):       Total Cost = ₹{total_cost_bayes:,.2f}")
    print(f"--> Cost Reduction vs Naive:   {(1 - total_cost_bayes / total_cost_naive) * 100:.1f}%")
    print(f"--> Cost Reduction vs Strict:  {(1 - total_cost_bayes / total_cost_strict) * 100:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    evaluate()