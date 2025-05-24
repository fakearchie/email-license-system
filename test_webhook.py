import httpx
import hmac
import hashlib
import base64
import json
import os
import sys

# Load environment variables or config
SHOPIFY_WEBHOOK_SECRET = os.environ.get("SHOPIFY_WEBHOOK_SECRET", "testsecret")
SHOPIFY_SHOP_DOMAIN = os.environ.get("SHOPIFY_SHOP_DOMAIN", "testshop.myshopify.com")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "http://localhost:8000/webhook/order/paid")

# Example Shopify order paid payload
order_data = {
    "id": 5182282154197,
    "email": "taio201021@gmail.com",
    "order_number": "1001",
    "line_items": [
        {
            "id": 13765142462661,
            "product_id": 8377160843557,
            "variant_id": 45235486679253,
            "title": "Basic License",
            "quantity": 1,
            "price": "29.99"
        }
    ]
}

def generate_hmac(data: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode('utf-8'), data, hashlib.sha256).digest()
    return base64.b64encode(digest).decode('utf-8')

async def send_shopify_test_webhook():
    json_data = json.dumps(order_data, separators=(",", ":"))
    hmac_signature = generate_hmac(json_data.encode('utf-8'), SHOPIFY_WEBHOOK_SECRET)
    headers = {
        "X-Shopify-Hmac-SHA256": hmac_signature,
        "X-Shopify-Shop-Domain": SHOPIFY_SHOP_DOMAIN,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(WEBHOOK_URL, headers=headers, data=json_data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_shopify_test_webhook())
