"""
PR BRANCH: feature/discount-refactor
Introduces a division-by-zero bug in calculate_discount() that raises
ZeroDivisionError for any coupon code, spiking the error rate in New Relic.

To simulate the bug PR:
  1. Replace the calculate_discount function in app.py with the one below.
  2. Run the service and traffic generator.
  3. Watch error rate climb in New Relic as coupon requests all fail.

Root cause: the refactor mistakenly divides by (1 - rate) instead of
multiplying, and when rate == 1.0 (a hypothetical 100% coupon) it would
be ZeroDivisionError. But worse, the lookup table was accidentally
replaced with a list, so .get() is gone and a TypeError fires on every
single request that passes a coupon_code.
"""


def calculate_discount_buggy(price, coupon_code):
    """BUG: discounts is now a list, not a dict — .get() raises AttributeError."""
    discounts = [
        ("SAVE10", 0.10),
        ("SAVE20", 0.20),
        ("HALFOFF", 0.50),
    ]
    # BUG: list has no .get() method → AttributeError on every coupon request
    rate = discounts.get(coupon_code, 0.0)
    return price * (1 - rate)
