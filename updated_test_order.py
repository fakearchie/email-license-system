import httpx
import hmac
import hashlib
import base64
import json
import asyncio
import os
import sys
from app.config import Settings
from app.services import supabase_service

settings = Settings()

# Your Vercel URL (replace this with your actual Vercel URL)
VERCEL_URL = "https://webhook-43060swbu-spotlights-projects-5455652f.vercel.app"

# Add diagnostics
print(f"Testing against URL: {VERCEL_URL}")
print(f"Python version: {sys.version}")
print(f"Command line args: {sys.argv}")
print(f"SHOPIFY_WEBHOOK_SECRET exists: {'SHOPIFY_WEBHOOK_SECRET' in os.environ}")
print(f"SUPABASE_URL exists: {'SUPABASE_URL' in os.environ}")

def generate_hmac(data: bytes, secret: str) -> str:
    """Generate Shopify HMAC signature"""
    digest = hmac.new(
        secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode('utf-8')

# Sample order payload
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

async def send_test_order():
    """Send a test order webhook"""
    # Ensure consistent JSON formatting
    json_data = json.dumps(order_data, separators=(',', ':'))  # Remove whitespace
    hmac_signature = generate_hmac(json_data.encode('utf-8'), settings.SHOPIFY_WEBHOOK_SECRET)
    
    print(f"Testing webhook endpoint: {VERCEL_URL}/webhook/order/paid")
    print(f"Generated HMAC: {hmac_signature}")
    print(f"Using secret: {settings.SHOPIFY_WEBHOOK_SECRET}")
    
    headers = {
        "X-Shopify-Hmac-SHA256": hmac_signature,
        "X-Shopify-Shop-Domain": settings.SHOPIFY_SHOP_DOMAIN,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False) as client:  # Added verify=False for testing
        try:
            response = await client.post(
                f"{VERCEL_URL}/webhook/order/paid",
                headers=headers,
                json=order_data,
                follow_redirects=True  # Added to handle Vercel redirects
            )
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")

async def test_supabase_connection():
    """Test the connection to Supabase"""
    print("\nTesting Supabase connection...")
    try:
        # Generate a test license key
        test_key = "TEST-KEY-" + os.urandom(4).hex()
        
        # Store the test key
        result = await supabase_service.store_license_key(
            license_key=test_key,
            category="test",
            email="test@example.com",
            order_id="TEST-1",
            product_id="TEST-PROD-1",
            product_name="Test Product"
        )
        
        if result["success"]:
            print("✅ Successfully stored test license key in Supabase")
        else:
            print(f"❌ Failed to store test license key: {result.get('error', 'Unknown error')}")
        
        # Retrieve the test key
        verify_result = await supabase_service.verify_license_key(test_key)
        
        if verify_result["success"]:
            print("✅ Successfully retrieved test license key from Supabase")
            print(f"License key data: {verify_result['data']}")
        else:
            print(f"❌ Failed to retrieve test license key: {verify_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing Supabase: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-supabase":
        asyncio.run(test_supabase_connection())
    else:
        asyncio.run(send_test_order())
