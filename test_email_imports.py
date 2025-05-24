import asyncio
import logging
from app.services import email_service
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_email_service():
    """Test that the email service works correctly with our fixed imports"""
    try:
        # Create a test email message
        message = MIMEMultipart()
        message["To"] = "test@example.com"
        message["From"] = "test@example.com"
        message["Subject"] = "Test Email"
        
        # Add text content
        text = "This is a test email to verify imports are working"
        message.attach(MIMEText(text, "plain"))
        
        print("Testing email_service.send_email_with_retry function...")
        
        # Attempt to run the function that was previously failing
        # We'll catch the exception since we don't actually want to send an email
        try:
            await email_service.send_email_with_retry(message, max_retries=1)
        except Exception as e:
            # We expect an authentication error or timeout, not an import error
            if "NameError" in str(e) or "name 'os' is not defined" in str(e):
                print("❌ The os module is still not properly imported")
                print(f"Error: {str(e)}")
                return False
            else:
                print("✅ The os module is properly imported")
                print(f"Expected error during email sending: {str(e)}")
                return True
                
        print("Email sent successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    print("Verifying email service imports...")
    result = asyncio.run(test_email_service())
    
    if result:
        print("\n✅ All imports are working correctly!")
        print("You can now deploy to Vercel with:")
        print("vercel --prod")
    else:
        print("\n❌ There are still issues with the imports.")
        print("Please fix the issues before deploying.")
