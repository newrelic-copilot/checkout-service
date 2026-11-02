import unittest
from unittest.mock import patch

with patch("newrelic.agent.initialize"):
    from app import app, calculate_discount


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

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

    @patch("app.time.sleep")
    def test_checkout_bulk_discount_totals(self, mock_sleep):
        for quantity, bulk_rate in (
            (2, 0.0),
            (3, 0.0),
            (4, 0.0),
            (5, 0.05),
            (6, 0.0),
            (9, 0.0),
            (10, 0.10),
            (11, 0.0),
            (50, 0.0),
        ):
            for coupon, coupon_rate in (("", 0.0), ("SAVE10", 0.10)):
                with self.subTest(quantity=quantity, coupon=coupon):
                    response = self.client.post("/checkout", json={
                        "product_id": "item-003",
                        "quantity": quantity,
                        "coupon_code": coupon,
                    })

                    self.assertEqual(response.status_code, 200)
                    result = response.get_json()
                    self.assertEqual(result["status"], "success")
                    self.assertEqual(
                        result["total"],
                        round(79.99 * quantity * (1 - coupon_rate) * (1 - bulk_rate), 2),
                    )

    def test_checkout_handles_inventory_tuple(self):
        for quantity in (1, 40, 41, 50):
            with self.subTest(quantity=quantity):
                response = self.client.post("/checkout", json={
                    "product_id": "item-001",
                    "quantity": quantity,
                })

                self.assertEqual(response.status_code, 200)
                result = response.get_json()
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["product"], "Laptop")
                self.assertEqual(result["quantity"], quantity)
                self.assertEqual(result["total"], round(999.99 * quantity, 2))
                self.assertRegex(result["order_id"], r"^ORD-\d{5}$")

    def test_checkout_preserves_validation_errors(self):
        for payload, message in (
            ({"product_id": "missing"}, "Product missing not found"),
            ({"quantity": 51}, "Insufficient stock for item-001"),
            ({"card_number": "123"}, "Invalid card number"),
            ({"quantity": 0}, "Amount must be positive"),
        ):
            with self.subTest(payload=payload):
                response = self.client.post("/checkout", json=payload)

                self.assertEqual(response.status_code, 400)
                result = response.get_json()
                self.assertEqual(result["status"], "error")
                self.assertIn(message, result["message"])


if __name__ == "__main__":
    unittest.main()
