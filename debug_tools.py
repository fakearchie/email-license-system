#!/usr/bin/env python
"""
Debug tools for testing the webhook and email functionality
"""
import httpx
import asyncio
import hmac
import hashlib
import base64
import json
import os
from dotenv import load_dotenv
import sys
import argparse

# Load environment variables
load_dotenv()

# Webhook URL - default to localhost for testing
DEFAULT_BASE_URL = "http://localhost:8000"


def generate_hmac(data: bytes, secret: str) -> str:
    """Generate Shopify HMAC signature"""
    digest = hmac.new(
        secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode('utf-8')


# Sample order payload
def get_test_order(email=None):
    return {
        "id": 5182282154197,
        "email": email or os.environ.get("TEST_EMAIL", "test@example.com"),
        "order_number": "1001",
        "line_items": [
            {
                "id": 13765142462661,
                "product_id": "8377160843557",
                "variant_id": 45235486679253,
                "title": "Basic License",
                "quantity": 1,
                "price": "29.99"
            }
        ]
    }


async def send_test_webhook(base_url=None):
    """Send a test webhook to the API"""
    base_url = base_url or DEFAULT_BASE_URL
    webhook_secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET")
    
    if not webhook_secret:
        print("Error: SHOPIFY_WEBHOOK_SECRET not found in environment")
        sys.exit(1)
    
    order_data = get_test_order()
    
    # Ensure consistent JSON formatting
    json_data = json.dumps(order_data, separators=(',', ':'))  # Remove whitespace
    hmac_signature = generate_hmac(json_data.encode('utf-8'), webhook_secret)
    
    url = f"{base_url}/webhook/order/paid"
    print(f"Testing webhook endpoint: {url}")
    print(f"Generated HMAC: {hmac_signature}")
    print(f"Using secret length: {len(webhook_secret)} chars")
    
    headers = {
        "X-Shopify-Hmac-SHA256": hmac_signature,
        "X-Shopify-Shop-Domain": os.environ.get("SHOPIFY_SHOP_DOMAIN", "example.myshopify.com"),
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, content=json_data, headers=headers)
            print(f"Response status: {r.status_code}")
            print(f"Response body: {r.text}")
            return r
    except Exception as e:
        print(f"Error sending webhook: {str(e)}")
        return None


async def test_health_endpoint(base_url=None):
    """Test the health endpoint"""
    base_url = base_url or DEFAULT_BASE_URL
    url = f"{base_url}/health"
    
    try:
        print(f"Checking health at: {url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
            print(f"Health endpoint status: {r.status_code}")
            
            # Try to parse as JSON, but handle case where it's not JSON
            try:
                json_response = r.json()
                print(f"Response (JSON): {json_response}")
                return json_response
            except:
                # If not JSON, print the raw text
                print(f"Response (text): {r.text}")
                return r.text
    except httpx.RequestError as e:
        print(f"Request error checking health: {str(e)}")
        return None
    except Exception as e:
        print(f"Error checking health: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        return None


async def test_email_endpoint(email=None, base_url=None):
    """Test the email diagnostic endpoint"""
    base_url = base_url or DEFAULT_BASE_URL
    email = email or os.environ.get("TEST_EMAIL", "test@example.com")
    url = f"{base_url}/diagnostic/email-test?email={email}"
    
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            print(f"Email test endpoint status: {r.status_code}")
            print(f"Response: {r.json() if r.status_code == 200 else r.text}")
            return r
    except Exception as e:
        print(f"Error testing email: {str(e)}")
        return None


async def test_root_endpoint(base_url=None):
    """Test the basic root endpoint"""
    base_url = base_url or DEFAULT_BASE_URL
    url = f"{base_url}/"
    
    try:
        print(f"Checking root endpoint at: {url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
            print(f"Root endpoint status: {r.status_code}")
            
            # Try to parse as JSON, but handle case where it's not JSON
            try:
                json_response = r.json()
                print(f"Response (JSON): {json_response}")
                return json_response
            except:
                # If not JSON, print the raw text
                print(f"Response (text): {r.text}")
                return r.text
    except Exception as e:
        print(f"Error checking root endpoint: {str(e)}")
        return None


async def main():
    parser = argparse.ArgumentParser(description='Debug tools for webhook system')
    parser.add_argument('--url', help='Base URL for testing (default: http://localhost:8000)')
    parser.add_argument('--email', help='Email address to use for testing')
    parser.add_argument('--test', choices=['webhook', 'health', 'email', 'root', 'all'], 
                        default='all', help='Test to run')
    
    args = parser.parse_args()
    base_url = args.url or DEFAULT_BASE_URL
    email = args.email
    
    if args.test == 'all' or args.test == 'health':
        print("\n=== Testing Health Endpoint ===")
        await test_health_endpoint(base_url)
    
    if args.test == 'all' or args.test == 'email':
        print("\n=== Testing Email Endpoint ===")
        await test_email_endpoint(email, base_url)
    
    if args.test == 'all' or args.test == 'webhook':
        print("\n=== Testing Webhook Endpoint ===")
        await send_test_webhook(base_url)
    
    if args.test == 'all' or args.test == 'root':
        print("\n=== Testing Root Endpoint ===")
        await test_root_endpoint(base_url)


if __name__ == "__main__":
    asyncio.run(main())
