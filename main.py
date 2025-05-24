from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from app.config import Settings
from app.services import email_service, license_service
from app.utils.shopify import verify_webhook

app = FastAPI(title="License Key Delivery System")
settings = Settings()

@app.on_event("startup")
async def startup_event():
    print("Application started")
    print(f"SMTP Settings: {settings.SMTP_HOST}:{settings.SMTP_PORT}")

@app.post("/webhook/order/paid")
async def handle_order_paid(request: Request):
    try:
        if not await verify_webhook(request, settings.SHOPIFY_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        order_data = await request.json()
        summary = []
        for item in order_data.get("line_items", []):
            try:
                product_id = str(item["product_id"])
                category = await license_service.get_product_category(product_id)
                try:
                    license_key = await license_service.pop_license_key(category)
                    await email_service.send_license_email(
                        customer_email=order_data["email"],
                        order_number=order_data["order_number"],
                        product_name=item["title"],
                        license_key=license_key
                    )
                    summary.append(f"License for category '{category}' sent to {order_data['email']}")
                except Exception as e:
                    await email_service.send_out_of_stock_email(
                        customer_email=order_data["email"],
                        product_name=item["title"],
                        category=category
                    )
                    summary.append(f"No license available for category '{category}' (notified {order_data['email']})")
            except Exception as e:
                return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
        return JSONResponse(content={"status": "success", "message": "\n".join(summary)}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

@app.post("/licenses/add/{category}")
async def add_licenses(category: str, licenses: str = None):
    import json
    try:
        if licenses is None:
            return {"status": "error", "detail": "No licenses provided"}
        try:
            keys = json.loads(licenses)
            if not isinstance(keys, list):
                raise ValueError
        except Exception:
            keys = [k.strip() for k in licenses.splitlines() if k.strip()]
        await license_service.add_licenses(category, keys)
        return {"status": "success", "added": len(keys)}
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/verify-license/{license_key}")
async def verify_license(license_key: str):
    result = await license_service.verify_license_key(license_key)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="License key not found")
    return {
        "valid": result["is_valid"],
        "details": result["data"]
    }

@app.get("/")
async def root():
    return {"message": "License Key Delivery API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
