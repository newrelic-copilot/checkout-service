import unittest
from unittest.mock import patch

with patch("newrelic.agent.initialize"):
    from app import app, calculate_discount


class CheckoutTests(unittest.TestCase):
    def test_calculate_discount(self):
        for coupon, expected in (
            ("SAVE10", 90.0),
            ("SAVE20", 80.0),
            ("HALFOFF", 50.0),
            ("UNKNOWN", 100.0),
            ("", 100.0),
        ):
            with self.subTest(coupon=coupon):
                self.assertAlmostEqual(calculate_discount(100.0, coupon), expected)

    def test_checkout_coupon_totals(self):
        with app.test_client() as client:
            for coupon, expected in (
                ("SAVE10", 143.98),
                ("SAVE20", 127.98),
                ("HALFOFF", 79.99),
                ("UNKNOWN", 159.98),
                ("", 159.98),
            ):
                with self.subTest(coupon=coupon):
                    response = client.post("/checkout", json={
                        "product_id": "item-003",
                        "quantity": 2,
                        "coupon_code": coupon,
                    })
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_json()["status"], "success")
                    self.assertEqual(response.get_json()["total"], expected)

    def test_invalid_payment_with_coupon_remains_client_error(self):
        with app.test_client() as client:
            response = client.post("/checkout", json={
                "coupon_code": "SAVE10",
                "card_number": "123",
            })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["message"], "Invalid card number")


if __name__ == "__main__":
    unittest.main()
