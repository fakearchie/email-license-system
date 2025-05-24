import hmac
import hashlib
import base64
from fastapi import Request

async def verify_webhook(request: Request, webhook_secret: str) -> bool:
    """Verify Shopify webhook signature (raw body, no re-encoding)"""
    hmac_header = request.headers.get('X-Shopify-Hmac-SHA256')
    if not hmac_header:
        return False

    body = await request.body()
    request._body = body  # Allow re-reading if needed

    digest = hmac.new(
        webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest).decode('utf-8')

    return hmac.compare_digest(computed_hmac, hmac_header)
