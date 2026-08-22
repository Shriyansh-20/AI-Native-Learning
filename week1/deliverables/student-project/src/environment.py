import random
import json
import pandas as pd
import numpy as np

np.random.seed(42)
random.seed(42)

HIDDEN_STATES = ["S1_HEALTHY", "S2_BENIGN_DRIFT", "S3_FORMAT_GLITCH", "S4_CORRUPTED"]

def generate_batch(batch_id: int, state: str, size: int = 100) -> dict:
    rows = []
    base_time = pd.Timestamp("2026-08-16 09:00:00")
    
    for i in range(size):
        tx_id = f"TX_{batch_id}_{i+1:04d}"
        t_offset = pd.Timedelta(seconds=i * 15)
        dt = base_time + t_offset
        
        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        sender = f"ACC_{random.randint(1000, 9999)}"
        receiver = f"ACC_{random.randint(1000, 9999)}"
        amount = round(float(np.random.exponential(scale=1200.0) + 10.0), 2)
        currency = "INR"
        status = "SUCCESS" if random.random() > 0.05 else "PENDING"
        
        if state == "S1_HEALTHY":
            pass # clean normal row
            
        elif state == "S2_BENIGN_DRIFT":
            # Legitimate promotional surge: 3.2x higher amounts, occasional lowercase currency
            amount = round(amount * 3.2, 2)
            currency = "inr" if random.random() > 0.5 else "INR"
            
        elif state == "S3_FORMAT_GLITCH":
            # Recoverable formatting: dates as DD/MM/YYYY, extra whitespace in status
            if random.random() < 0.6:
                timestamp_str = dt.strftime("%d/%m/%Y %H:%M:%S")
            if random.random() < 0.4:
                status = " SUCCESS "
                
        elif state == "S4_CORRUPTED":
            # Critical semantic corruption: negative amounts or null receivers
            if random.random() < 0.05:
                corruption_type = random.choice(["negative_amount", "extreme_overflow", "null_receiver"])
                if corruption_type == "negative_amount":
                    amount = -round(abs(amount), 2)
                elif corruption_type == "extreme_overflow":
                    amount = 99999999.00
                elif corruption_type == "null_receiver":
                    receiver = None
                    
        rows.append({
            "transaction_id": tx_id,
            "timestamp": timestamp_str,
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": amount,
            "currency": currency,
            "status": status
        })
        
    return {
        "batch_id": batch_id,
        "true_state": state,
        "records": rows
    }

def generate_test_suite(total_batches: int = 40) -> list:
    distribution = (
        ["S1_HEALTHY"] * 24 +
        ["S2_BENIGN_DRIFT"] * 6 +
        ["S3_FORMAT_GLITCH"] * 5 +
        ["S4_CORRUPTED"] * 5
    )
    random.shuffle(distribution)
    
    test_cases = []
    for idx, state in enumerate(distribution, 1):
        test_cases.append(generate_batch(idx, state, size=100))
        
    return test_cases

if __name__ == "__main__":
    suite = generate_test_suite(40)
    with open("data/test_batches.json", "w") as f:
        json.dump(suite, f, indent=2)
    print("Generated 40 test batches in data/test_batches.json")