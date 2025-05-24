import hmac
import hashlib
import base64
import json
from fastapi import Request

async def verify_webhook(request: Request, webhook_secret: str) -> bool:
    """Verify Shopify webhook signature"""
    
    # Get the HMAC header
    hmac_header = request.headers.get('X-Shopify-Hmac-SHA256')
    if not hmac_header:
        return False
        
    # Get request body (don't consume it)
    body = await request.body()
    request._body = body  # Store body back into request to allow re-reading
    body_str = body.decode('utf-8')
    
    # Format JSON consistently
    try:
        parsed_json = json.loads(body_str)
        body_str = json.dumps(parsed_json, separators=(',', ':'))
    except:
        pass  # Use body as-is if not valid JSON    # Calculate HMAC
    digest = hmac.new(
        webhook_secret.encode('utf-8'),
        body_str.encode('utf-8'),
        hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest).decode('utf-8')
    
    # Compare HMACs
    return hmac.compare_digest(computed_hmac, hmac_header)
