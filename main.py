from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os

from app.config import Settings
from app.services import email_service, license_service, supabase_service
from app.utils.shopify import verify_webhook

app = FastAPI(title="License Key Delivery System")
settings = Settings()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Application started")
    logger.info(f"SMTP Settings: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL}")

@app.post("/webhook/order/paid")
async def handle_order_paid(request: Request):
    try:
        if not await verify_webhook(request, settings.SHOPIFY_WEBHOOK_SECRET):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        order_data = await request.json()
        logger.info(f"Received order data: {order_data}")
        
        for item in order_data.get("line_items", []):
            try:
                # Get product details and category
                product_id = str(item["product_id"])
                category = await license_service.get_product_category(product_id)
                order_id = str(order_data["order_number"])
                
                # Generate a license key 
                license_key = await license_service.generate_license_key(category, order_id, product_id)
                logger.info(f"Generated license key: {license_key} for category {category}")
                
                # Store license key in Supabase
                result = await license_service.store_license_key(
                    license_key=license_key,
                    category=category,
                    email=order_data["email"],
                    order_id=order_id,
                    product_id=product_id,
                    product_name=item["title"]
                )
                
                if not result["success"]:
                    logger.error(f"Failed to store license key: {result.get('error')}")
                
                # Send email with the generated license key
                await email_service.send_license_email(
                    customer_email=order_data["email"],
                    order_number=order_data["order_number"],
                    product_name=item["title"],
                    license_key=license_key
                )
                
                logger.info(f"License key delivered for order {order_data['order_number']}")
            except Exception as e:
                logger.error(f"Error processing line item: {str(e)}")
                return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
        
        return JSONResponse(content={"status": "success"}, status_code=200)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

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
