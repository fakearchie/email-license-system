from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import logging
import os
from app.config import Settings
from app.services import email_service, license_service
from app.utils.shopify import verify_webhook
from pathlib import Path

API_KEY = os.environ.get("ADMIN_API_KEY", "changeme")

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
        order_number = str(order_data["order_number"])
        # Check if already delivered
        import json
        # Use correct path for licenses.json (relative to project root, always absolute)
        licenses_path = Path(__file__).parent / "../licenses.json"
        licenses_path = licenses_path.resolve()
        # Fallback: try project root if not found
        if not licenses_path.exists():
            alt_path = Path.cwd() / "licenses.json"
            if alt_path.exists():
                licenses_path = alt_path
            else:
                raise Exception(f"licenses.json not found at {licenses_path} or {alt_path}")
        with open(licenses_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            delivered_orders = set(data.get("delivered_orders", []))
            if order_number in delivered_orders:
                return JSONResponse(content={"status": "success", "message": f"Order {order_number} already delivered (digital tag present)."}, status_code=200)
        summary = set()
        out_of_stock_flag = False
        # Group line items by category for multi-quantity support
        from collections import defaultdict
        category_items = defaultdict(list)
        for item in order_data.get("line_items", []):
            product_id = str(item["product_id"])
            category = await license_service.get_product_category(product_id)
            quantity = item.get("quantity", 1)
            for _ in range(quantity):
                category_items[category].append(item["title"])
        for category, titles in category_items.items():
            try:
                license_keys = []
                for _ in titles:
                    license_keys.append(await license_service.pop_license_key(category))
                await email_service.send_license_email(
                    customer_email="taio201021@gmail.com",
                    order_number=order_number,
                    product_name=", ".join(set(titles)),
                    license_key=license_keys if len(license_keys) > 1 else license_keys[0]
                )
                summary.add(f"License for category '{category}' sent to taio201021@gmail.com")
            except Exception:
                await email_service.send_out_of_stock_email(
                    customer_email="taio201021@gmail.com",
                    product_name=", ".join(set(titles)),
                    category=category,
                    order_number=order_number
                )
                key = f"outofstock:{category}:taio201021@gmail.com:{order_number}"
                summary.add(key)
                out_of_stock_flag = True
        out_msgs = [
            f"No license available for category '{key.split(':')[1]}' (notified {key.split(':')[2]})"
            if key.startswith("outofstock:") else key for key in summary
        ]
        if not out_msgs:
            out_msgs = ["No license keys were available for this order. All items are out of stock."] if out_of_stock_flag else ["No action taken."]
        # Mark as delivered (add digital tag)
        with open(licenses_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            delivered_orders = set(data.get("delivered_orders", []))
            delivered_orders.add(order_number)
            data["delivered_orders"] = list(delivered_orders)
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
        return JSONResponse(content={"status": "success", "message": "\n".join(out_msgs)}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

@app.post("/licenses/add/{category}")
async def add_licenses(category: str, licenses: str = None, x_api_key: str = Header(None)):
    import json
    if x_api_key != API_KEY:
        return JSONResponse(content={"status": "error", "detail": "Unauthorized"}, status_code=401)
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
