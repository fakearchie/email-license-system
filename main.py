from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os

from app.config import Settings
from app.services import email_service, license_service
from app.utils.shopify import verify_webhook

app = FastAPI(title="License Key Delivery System")
settings = Settings()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Application started")
    logger.info(f"SMTP Settings: {settings.SMTP_HOST}:{settings.SMTP_PORT}")

@app.post("/webhook/order/paid")
async def handle_order_paid(request: Request):
    try:
        if not await verify_webhook(request, settings.SHOPIFY_WEBHOOK_SECRET):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        order_data = await request.json()
        summary = []
        for item in order_data.get("line_items", []):
            try:
                product_id = str(item["product_id"])
                category = await license_service.get_product_category(product_id)
                try:
                    license_key = await license_service.pop_license_key(category)
                    logger.info(f"Assigned license key: {license_key} for category {category}")
                    await email_service.send_license_email(
                        customer_email=order_data["email"],
                        order_number=order_data["order_number"],
                        product_name=item["title"],
                        license_key=license_key
                    )
                    logger.info(f"License key delivered for order {order_data['order_number']}")
                    summary.append(f"License for category '{category}' sent to {order_data['email']}")
                except Exception as e:
                    # Out of stock: send notification email
                    logger.error(f"Error assigning license: {str(e)}")
                    await email_service.send_out_of_stock_email(
                        customer_email=order_data["email"],
                        product_name=item["title"],
                        category=category
                    )
                    summary.append(f"No license available for category '{category}' (notified {order_data['email']})")
            except Exception as e:
                logger.error(f"Error processing line item: {str(e)}")
                return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
        # Only one message in response, joined by newlines
        return JSONResponse(content={"status": "success", "message": "\n".join(summary)}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

@app.post("/licenses/add/{category}")
async def add_licenses(category: str, licenses: str = None):
    """Add license keys to a category. Accepts a plain text list (one per line) or JSON array."""
    from fastapi import Request
    from fastapi import Form
    from fastapi import Body
    import json
    try:
        # Accept both JSON array and plain text
        if licenses is None:
            return {"status": "error", "detail": "No licenses provided"}
        try:
            # Try to parse as JSON array
            keys = json.loads(licenses)
            if not isinstance(keys, list):
                raise ValueError
        except Exception:
            # Fallback: treat as plain text, one key per line
            keys = [k.strip() for k in licenses.splitlines() if k.strip()]
        await license_service.add_licenses(category, keys)
        return {"status": "success", "added": len(keys)}
    except Exception as e:
        logger.error(f"Error adding licenses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint for testing the application"""
    return {"status": "ok"}

@app.get("/verify-license/{license_key}")
async def verify_license(license_key: str):
    """Verify if a license key is valid"""
    result = await license_service.verify_license_key(license_key)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="License key not found")
    
    return {
        "valid": result["is_valid"],
        "details": result["data"]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "License Key Delivery API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
