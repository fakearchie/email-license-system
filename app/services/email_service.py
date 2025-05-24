from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os
import ssl
import time
from app.config import Settings

settings = Settings()

OUT_OF_STOCK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 0; }
        .container { max-width: 520px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px #0001; padding: 32px 24px; }
        h1 { font-size: 24px; font-weight: 700; color: #d7263d; margin-bottom: 16px; }
        .message { font-size: 16px; margin-bottom: 24px; }
        .category { font-size: 15px; color: #555; margin-bottom: 8px; }
        .footer { margin-top: 32px; font-size: 13px; color: #888; border-top: 1px solid #eee; padding-top: 16px; }
        .support { color: #d7263d; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>We're Out of License Keys</h1>
        <div class="message">Hello,<br><br>Thank you for your order of <b>{{ product_name }}</b>.<br><br>Unfortunately, we are currently out of license keys for the <span class="category">{{ category }}</span> category.<br><br>We will send your license key as soon as more become available.<br><br>If you have any questions, please <a href="mailto:support@example.com" class="support">contact support</a>.<br><br>We apologize for the inconvenience.</div>
        <div class="footer">&copy; {{ current_year }} Spotlight. All rights reserved.</div>
    </div>
</body>
</html>
"""

async def send_license_email(
    customer_email: str,
    order_number: str,
    product_name: str,
    license_key: str
) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your License Key - Order #{order_number}"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = customer_email
        from datetime import datetime
        current_year = datetime.now().year
        from app.services.email_service import EMAIL_TEMPLATE
        template = Template(EMAIL_TEMPLATE)
        html_content = template.render(
            order_number=order_number,
            product_name=product_name,
            license_key=license_key,
            shop_domain=settings.SHOPIFY_SHOP_DOMAIN.strip('/'),
            current_year=current_year
        )
        message.attach(MIMEText(html_content, "html"))
        await send_email_with_retry(message)
    except Exception as e:
        import logging
        logging.error(f"Email sending failed: {str(e)}")

async def send_out_of_stock_email(
    customer_email: str,
    product_name: str,
    category: str
) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"We're out of license keys for {product_name} ({category})"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = customer_email
        from datetime import datetime
        current_year = datetime.now().year
        template = Template(OUT_OF_STOCK_TEMPLATE)
        html_content = template.render(
            product_name=product_name,
            category=category,
            current_year=current_year
        )
        message.attach(MIMEText(html_content, "html"))
        await send_email_with_retry(message)
    except Exception as e:
        import logging
        logging.error(f"Out-of-stock email failed: {str(e)}")

async def send_email_with_retry(message, max_retries=3):
    import logging
    retries = 0
    last_error = None
    while retries < max_retries:
        try:
            import ssl
            use_tls = settings.SMTP_PORT == 465
            smtp = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=use_tls,
                tls_context=ssl.create_default_context(),
                timeout=30
            )
            await smtp.connect()
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            return
        except Exception as e:
            retries += 1
            last_error = e
            time.sleep(2 ** retries)
    import logging
    logging.error(f"Email send failed after retries: {str(last_error)}")
