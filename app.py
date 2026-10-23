import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

import random
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

PRODUCTS = {
    "item-001": {"name": "Laptop", "price": 999.99, "stock": 50},
    "item-002": {"name": "Phone", "price": 499.99, "stock": 100},
    "item-003": {"name": "Headphones", "price": 79.99, "stock": 200},
    "item-004": {"name": "Tablet", "price": 349.99, "stock": 75},
}


def calculate_discount(price, coupon_code):
    """Apply discount based on coupon code."""
    discounts = [
        ("SAVE10", 0.10),
        ("SAVE20", 0.20),
        ("HALFOFF", 0.50),
    ]
    rate = discounts.get(coupon_code, 0.0)
    return price * (1 - rate)


def validate_payment(card_number, amount):
    """Validate payment details."""
    if not card_number or len(str(card_number)) < 16:
        raise ValueError("Invalid card number")
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return True


LOW_STOCK_THRESHOLD = 10


def process_inventory(product_id, quantity):
    """Check inventory and report whether the item is running low."""
    product = PRODUCTS.get(product_id)
    if not product:
        raise KeyError(f"Product {product_id} not found")
    if product["stock"] < quantity:
        raise ValueError(f"Insufficient stock for {product_id}")
    low_stock = product["stock"] - quantity < LOW_STOCK_THRESHOLD
    return product, low_stock


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/checkout", methods=["POST"])
@newrelic.agent.background_task()
def checkout():
    data = request.get_json(force=True)

    product_id = data.get("product_id", "item-001")
    quantity = int(data.get("quantity", 1))
    coupon_code = data.get("coupon_code", "")
    card_number = data.get("card_number", "4111111111111111")

    newrelic.agent.add_custom_attribute("product_id", product_id)
    newrelic.agent.add_custom_attribute("quantity", quantity)
    newrelic.agent.add_custom_attribute("coupon_code", coupon_code)

    try:
        product = process_inventory(product_id, quantity)

        unit_price = product["price"]
        total = unit_price * quantity

        if coupon_code:
            total = calculate_discount(total, coupon_code)

        validate_payment(card_number, total)

        order_id = f"ORD-{random.randint(10000, 99999)}"

        newrelic.agent.record_custom_event("CheckoutCompleted", {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "total": round(total, 2),
            "coupon_code": coupon_code or "none",
        })

        newrelic.agent.add_custom_attribute("order_id", order_id)
        newrelic.agent.add_custom_attribute("order_total", round(total, 2))

        return jsonify({
            "status": "success",
            "order_id": order_id,
            "product": product["name"],
            "quantity": quantity,
            "total": round(total, 2),
        }), 200

    except (KeyError, ValueError) as e:
        newrelic.agent.notice_error()
        newrelic.agent.record_custom_event("CheckoutFailed", {
            "product_id": product_id,
            "reason": str(e),
            "quantity": quantity,
        })
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        newrelic.agent.notice_error()
        newrelic.agent.record_custom_event("CheckoutFailed", {
            "product_id": product_id,
            "reason": "internal_error",
            "quantity": quantity,
        })
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/products", methods=["GET"])
def list_products():
    return jsonify({"products": list(PRODUCTS.keys())}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
