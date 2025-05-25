import requests
import json
import hmac
import base64
import os

SHOPIFY_WEBHOOK_SECRET = os.environ.get("SHOPIFY_WEBHOOK_SECRET", "1a3856d3d7c3086ed6b49fc32e326b51b03f71972e72136b7ea414bd1d4ff324")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://email-license-system-production.up.railway.app/webhook/order/paid")

def generate_hmac(data: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), data, "sha256").digest()
    return base64.b64encode(digest).decode()

def send_test_webhook():
    order_data = {
        "order_number": 123453,
        "email": "test@example.com",
        "line_items": [
            {"product_id": "15168702775561", "title": "Basic Product"},
            {"product_id": "8377160876325", "title": "Pro Product"}
        ]
    }
    data_bytes = json.dumps(order_data, separators=(",", ":")).encode("utf-8")
    hmac_header = generate_hmac(data_bytes, SHOPIFY_WEBHOOK_SECRET)
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Hmac-SHA256": hmac_header
    }
    response = requests.post(WEBHOOK_URL, data=data_bytes, headers=headers)
    print("Status:", response.status_code)
    print("Response:", response.text)

if __name__ == "__main__":
    send_test_webhook()
