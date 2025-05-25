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

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">\n<head>
    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <style>
        body { font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #ffffff; color: #1a1a1a; margin: 0; padding: 0; }
        .email-wrapper { width: 100%; max-width: 520px; margin: 0 auto; padding: 32px 24px; }
        h1 { font-size: 24px; font-weight: 600; margin: 0 0 32px; letter-spacing: -0.3px; color: #000000; }
        .order-details { font-size: 14px; color: #666666; margin: 24px 0; }
        .license-container { margin: 32px 0; text-align: center; }
        .license-key { display: inline-block; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 16px 24px; font-family: 'SF Mono', SFMono-Regular, ui-monospace, Menlo, Monaco, monospace; font-size: 15px; letter-spacing: 0.5px; color: #000000; margin-bottom: 8px; }
        .license-note { font-size: 13px; color: #666666; margin-top: 8px; }
        .button-container { margin: 24px 0 40px; }
        .button { display: inline-block; padding: 10px 20px; background-color: #000000; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 500; transition: all 0.2s ease; }
        .button:hover { background-color: #333333; }
        .footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #f1f1f1; font-size: 13px; color: #666666; }
        .help-text { margin-top: 32px; font-size: 14px; color: #666666; }
        .help-link { color: #000000; text-decoration: none; border-bottom: 1px solid #000000; }
    </style>
</head>
<body>
    <div class=\"email-wrapper\">
        <h1>Here's your license key</h1>
        <div class=\"order-details\">Order #{{ order_number }} • {{ product_name }}</div>
        <div class=\"license-container\">
            <div class=\"license-key\">{{ license_key }}</div>
            <div class=\"license-note\">Keep this key safe — you'll need it for activation</div>
        </div>
        <div class=\"button-container\" style=\"text-align: center;\">
            <a href=\"https://{{ shop_domain }}/account/orders/{{ order_number }}\" class=\"button\">View order details</a>
        </div>
        <div class=\"footer\">© {{ current_year }} Spotlight. All rights reserved.</div>
    </div>
</body>
</html>
"""

OUT_OF_STOCK_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <style>
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #222; margin: 0; padding: 0; }
        .container { max-width: 520px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px #0002; padding: 40px 32px; border: 1px solid #e0e0e0; }
        h1 { font-size: 26px; font-weight: 700; color: #b00020; margin-bottom: 18px; letter-spacing: -0.5px; }
        .message { font-size: 16px; margin-bottom: 24px; line-height: 1.7; color: #333; }
        .footer { margin-top: 32px; font-size: 13px; color: #888; border-top: 1px solid #eee; padding-top: 14px; }
        .alert { background: #fff3f3; border: 1px solid #ffcccc; color: #b00020; padding: 16px; border-radius: 8px; margin-bottom: 24px; font-size: 15px; }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Important: License Key Unavailable</h1>
        <div class=\"alert\">We regret to inform you that your license key is currently <b>out of stock</b>.</div>
        <div class=\"message\">
            Dear Customer,<br><br>
            We are currently unable to fulfill your license key request for order <b>#{{ order_number }}</b> (category: <b>{{ category }}</b>).<br><br>
            <b>This is a high-priority issue</b> and our team has been notified. You will receive your license key as soon as new stock is available.<br><br>
            We sincerely apologize for the inconvenience and appreciate your patience. If you have any questions or need urgent assistance, please reply to this email or contact our support team.
        </div>
        <div class=\"footer\">&copy; {{ current_year }} Spotlight. All rights reserved.</div>
    </div>
</body>
</html>
"""

default_current_year = 2025

async def send_license_email(
    customer_email: str,
    order_number: str,
    product_name: str,
    license_key: str | list[str]
) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your License Key - Order #{order_number}"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = customer_email
        from datetime import datetime
        try:
            current_year = datetime.now().year
        except Exception:
            current_year = default_current_year
        template = Template(EMAIL_TEMPLATE)
        # Support sending multiple keys in one email
        if isinstance(license_key, list):
            license_key_html = "".join([
                f'<div class="license-key">{key}</div>' for key in license_key
            ])
            html_content = template.render(
                order_number=order_number,
                product_name=product_name,
                license_key=license_key_html,
                shop_domain=settings.SHOPIFY_SHOP_DOMAIN.strip('/'),
                current_year=current_year
            )
        else:
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
    category: str,
    order_number: str
) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"License Key Out of Stock for Order #{order_number}"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = customer_email
        from datetime import datetime
        try:
            current_year = datetime.now().year
        except Exception:
            current_year = default_current_year
        template = Template(OUT_OF_STOCK_TEMPLATE)
        html_content = template.render(
            order_number=order_number,
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
