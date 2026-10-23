import unittest
from unittest.mock import patch

with patch("newrelic.agent.initialize"):
    import app


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

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
