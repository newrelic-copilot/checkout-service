"""
Continuous traffic generator for the checkout service.
Sends a mix of valid and edge-case requests to keep metrics flowing.
Run separately: python traffic_generator.py
"""

import random
import time
import requests

BASE_URL = "http://localhost:5001"

VALID_PRODUCTS = ["item-001", "item-002", "item-003", "item-004"]
INVALID_PRODUCTS = ["item-999", "item-000"]
COUPONS = ["SAVE10", "SAVE20", "HALFOFF", "", "", ""]  # empty = no coupon (weighted)

SCENARIOS = [
    # (weight, label, payload_fn)
    (60, "valid_purchase", lambda: {
        "product_id": random.choice(VALID_PRODUCTS),
        "quantity": random.randint(1, 3),
        "card_number": "4111111111111111",
        "coupon_code": random.choice(COUPONS),
    }),
    (15, "invalid_product", lambda: {
        "product_id": random.choice(INVALID_PRODUCTS),
        "quantity": 1,
        "card_number": "4111111111111111",
    }),
    (10, "bad_card", lambda: {
        "product_id": random.choice(VALID_PRODUCTS),
        "quantity": 1,
        "card_number": "123",  # too short — triggers validation error
    }),
    (10, "high_quantity", lambda: {
        "product_id": random.choice(VALID_PRODUCTS),
        "quantity": 500,        # exceeds stock — triggers stock error
        "card_number": "4111111111111111",
    }),
    (5, "zero_quantity", lambda: {
        "product_id": random.choice(VALID_PRODUCTS),
        "quantity": 0,
        "card_number": "4111111111111111",
    }),
]


def pick_scenario():
    weights = [s[0] for s in SCENARIOS]
    return random.choices(SCENARIOS, weights=weights, k=1)[0]


def send_request(session):
    weight, label, payload_fn = pick_scenario()
    payload = payload_fn()

    try:
        resp = session.post(f"{BASE_URL}/checkout", json=payload, timeout=5)
        status = resp.status_code
        result = "ok" if status == 200 else "err"
        print(f"[{label:18s}] {status} {result}  -> {resp.json().get('order_id', resp.json().get('message', ''))}")
    except requests.exceptions.ConnectionError:
        print("[traffic_gen] Service not reachable — retrying in 3s")
        time.sleep(3)
    except Exception as e:
        print(f"[traffic_gen] Unexpected error: {e}")


def wait_for_service(session, retries=20):
    for i in range(retries):
        try:
            resp = session.get(f"{BASE_URL}/health", timeout=3)
            if resp.status_code == 200:
                print("[traffic_gen] Service is up, starting traffic...")
                return True
        except Exception:
            pass
        print(f"[traffic_gen] Waiting for service ({i+1}/{retries})...")
        time.sleep(2)
    return False


def main():
    session = requests.Session()

    if not wait_for_service(session):
        print("[traffic_gen] Could not connect to service. Is it running?")
        return

    print("[traffic_gen] Sending continuous traffic. Press Ctrl+C to stop.\n")

    try:
        while True:
            send_request(session)
            time.sleep(random.uniform(0.3, 1.2))
    except KeyboardInterrupt:
        print("\n[traffic_gen] Stopped.")


if __name__ == "__main__":
    main()
