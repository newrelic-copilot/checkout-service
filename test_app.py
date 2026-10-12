import unittest

from app import app, calculate_discount


class CalculateDiscountTest(unittest.TestCase):
    def test_applies_known_coupon_discounts(self):
        self.assertEqual(calculate_discount(100.0, "SAVE10"), 90.0)
        self.assertEqual(calculate_discount(100.0, "SAVE20"), 80.0)
        self.assertEqual(calculate_discount(100.0, "HALFOFF"), 50.0)

    def test_unknown_coupon_keeps_original_price(self):
        self.assertEqual(calculate_discount(100.0, "UNKNOWN"), 100.0)

    def test_checkout_succeeds_with_coupon(self):
        response = app.test_client().post(
            "/checkout",
            json={"product_id": "item-001", "quantity": 1, "coupon_code": "SAVE10"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total"], 899.99)


if __name__ == "__main__":
    unittest.main()
