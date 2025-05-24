import asyncio
from app.services import supabase_service
from app.config import Settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
settings = Settings()

async def verify_supabase_setup():
    """Verify that the Supabase database is properly set up"""
    print(f"Checking Supabase connection to: {settings.SUPABASE_URL}")
    
    # Test storing a license key
    try:
        test_key = "SETUP-TEST-LICENSE-KEY"
        result = await supabase_service.store_license_key(
            license_key=test_key,
            category="test",
            email="setup@example.com",
            order_id="SETUP-1",
            product_id="SETUP-PROD",
            product_name="Setup Test Product"
        )
        
        if result["success"]:
            print("✅ Successfully stored license key in Supabase")
            
            # Verify we can retrieve it
            verify_result = await supabase_service.verify_license_key(test_key)
            if verify_result["success"]:
                print("✅ Successfully verified license key in Supabase")
                print("✅ Supabase is properly set up and working!")
            else:
                print(f"❌ Failed to verify license key: {verify_result.get('error')}")
        else:
            print(f"❌ Failed to store license key: {result.get('error')}")
            print("""
            Make sure you have:
            1. Created the 'license_keys' table in Supabase
            2. Set the SUPABASE_URL and SUPABASE_KEY environment variables
            3. Given proper permissions to the 'anon' key in Supabase
            """)
    
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        print("""
        Possible issues:
        1. Incorrect SUPABASE_URL or SUPABASE_KEY in environment variables
        2. Database tables not set up correctly
        3. Network connectivity issues
        
        Please check the DEPLOYMENT.md file for setup instructions.
        """)

if __name__ == "__main__":
    print("Verifying Supabase setup...")
    asyncio.run(verify_supabase_setup())
