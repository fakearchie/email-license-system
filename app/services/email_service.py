from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os
import ssl
import logging
import time
from app.config import Settings

settings = Settings()
logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">    <style>
        body {
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.5;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            -webkit-text-size-adjust: 100%;
            background-color: #ffffff;
        }
        .email-wrapper {
            width: 100%;
            max-width: 520px;
            margin: 0 auto;
            padding: 32px 24px;
        }
        h1 {
            font-size: 24px;
            font-weight: 600;
            margin: 0 0 32px;
            letter-spacing: -0.3px;
            color: #000000;
        }
        .order-details {
            font-size: 14px;
            color: #666666;
            margin: 24px 0;
        }
        .license-container {
            margin: 32px 0;
            text-align: center;
        }
        .license-key {
            display: inline-block;
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 16px 24px;
            font-family: "SF Mono", SFMono-Regular, ui-monospace, Menlo, Monaco, monospace;
            font-size: 15px;
            letter-spacing: 0.5px;
            color: #000000;
            margin-bottom: 8px;
        }
        .license-note {
            font-size: 13px;
            color: #666666;
            margin-top: 8px;
        }        .button-container {
            margin: 24px 0 40px;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #000000;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .button:hover {
            background-color: #333333;
        }
        .footer {
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid #f1f1f1;
            font-size: 13px;
            color: #666666;
        }
        .help-text {
            margin-top: 32px;
            font-size: 14px;
            color: #666666;
        }
        .help-link {
            color: #000000;
            text-decoration: none;
            border-bottom: 1px solid #000000;
        }
    </style>
</head>
<body>    <div class="email-wrapper">
        <h1>Here's your license key</h1>
        
        <div class="order-details">
            Order #{{ order_number }} • {{ product_name }}
        </div>
        
        <div class="license-container">
            <div class="license-key">{{ license_key }}</div>
            <div class="license-note">Keep this key safe — you'll need it for activation</div>        </div>
        
        <div class="button-container" style="text-align: center;">
            <a href="https://{{ shop_domain }}/account/orders/{{ order_number }}" class="button">View order details</a>
        </div>
        
        <div class="footer">
            © {{ current_year }} Spotlight. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

async def log_email_instead(
    customer_email: str,
    order_number: str,
    product_name: str,
    license_key: str
) -> None:
    """
    Fallback method to log email details instead of sending
    Useful for environments where SMTP is not available
    """
    logger.info("=" * 50)
    logger.info("EMAIL DELIVERY LOG (FALLBACK MODE)")
    logger.info("=" * 50)
    logger.info(f"To: {customer_email}")
    logger.info(f"Subject: Your License Key - Order #{order_number}")
    logger.info(f"Product: {product_name}")
    logger.info(f"License Key: {license_key}")
    logger.info("=" * 50)
    
    # Also save to a file if we're not on Vercel
    if os.environ.get("VERCEL") != "1":
        try:
            with open("email_log.txt", "a") as f:
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"To: {customer_email}\n")
                f.write(f"Subject: Your License Key - Order #{order_number}\n")
                f.write(f"Product: {product_name}\n")
                f.write(f"License Key: {license_key}\n")
                f.write("=" * 50 + "\n")
        except Exception as e:
            logger.error(f"Failed to write to email log: {str(e)}")

# Update the main send_license_email function to use the fallback
async def send_license_email(
    customer_email: str,
    order_number: str,
    product_name: str,
    license_key: str
) -> None:
    """Send license key email to customer with fallback mechanism"""
    
    # Check if we should use mock mode (for testing)
    if os.environ.get("USE_MOCK_EMAIL") == "1":
        logger.info("Using mock email mode - logging instead of sending")
        await log_email_instead(customer_email, order_number, product_name, license_key)
        return
    
    try:
        # Original email sending logic with additional try/except
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your License Key - Order #{order_number}"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = customer_email
        
        # Render HTML email
        template = Template(EMAIL_TEMPLATE)
        html_content = template.render(
            order_number=order_number,
            product_name=product_name,
            license_key=license_key,
            shop_domain=settings.SHOPIFY_SHOP_DOMAIN.strip('/'),
            current_year=2025
        )
        
        # Attach HTML content
        message.attach(MIMEText(html_content, "html"))
        
        # Send using SSL
        await send_email_with_retry(message)
        logger.info("Email sent successfully!")
        
    except Exception as e:
        import traceback
        logger.error(f"Email sending failed, using fallback: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Use fallback mechanism
        await log_email_instead(customer_email, order_number, product_name, license_key)

async def send_email_with_retry(message, max_retries=3):
    """Helper function to send email with retries"""
    logger = logging.getLogger(__name__)
    
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            # Check if we're on Vercel 
            is_vercel = os.environ.get("VERCEL") == "1"
            
            logger.info(f"SMTP Settings: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            logger.info(f"Sending email to: {message['To']}")
            logger.info(f"Running on Vercel: {is_vercel}")
            
            # Create SSL context explicitly
            ssl_context = ssl.create_default_context()
            
            # Use the correct port/TLS setting combo
            use_tls = settings.SMTP_PORT == 465  # True for 465 (SSL), False for 587 (STARTTLS)
            
            smtp = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=use_tls,
                tls_context=ssl_context,
                timeout=30  # Increase timeout for Vercel environment
            )
            
            logger.info(f"Connecting to SMTP server with use_tls={use_tls}...")
            await smtp.connect()
            if not use_tls:
                logger.info("Starting TLS...")
                await smtp.starttls()
            logger.info("Logging into SMTP server...")
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            logger.info("Sending message...")
            await smtp.send_message(message)
            logger.info("Quitting SMTP connection...")
            await smtp.quit()
            return  # Success, exit function
            
        except Exception as e:
            retries += 1
            last_error = e
            logger.warning(f"Email attempt {retries} failed: {str(e)}")
            if retries < max_retries:
                # Wait before retrying (exponential backoff)
                wait_time = 2 ** retries
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    # If we got here, all retries failed
    raise last_error
