from supabase import create_client, Client
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime

from app.config import Settings

settings = Settings()
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def store_license_key(
    license_key: str, 
    category: str, 
    email: str, 
    order_id: str, 
    product_id: str, 
    product_name: str
) -> Dict:
    """Store a license key in Supabase"""
    try:
        # Create record in 'license_keys' table
        response = supabase.table('license_keys').insert({
            'key': license_key,
            'category': category,
            'email': email,
            'order_id': order_id,
            'product_id': product_id,
            'product_name': product_name,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Supabase error: {response.error}")
            return {"success": False, "error": response.error}
        
        logger.info(f"License key {license_key} stored in Supabase")
        return {"success": True, "data": response.data}
    
    except Exception as e:
        logger.error(f"Error storing license key in Supabase: {str(e)}")
        return {"success": False, "error": str(e)}

async def get_license_key(license_key: str) -> Dict:
    """Retrieve a license key from Supabase"""
    try:
        response = supabase.table('license_keys').select('*').eq('key', license_key).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Supabase error: {response.error}")
            return {"success": False, "error": response.error}
        
        if not response.data:
            return {"success": False, "error": "License key not found"}
        
        return {"success": True, "data": response.data[0]}
    
    except Exception as e:
        logger.error(f"Error retrieving license key from Supabase: {str(e)}")
        return {"success": False, "error": str(e)}

async def get_license_keys_by_email(email: str) -> Dict:
    """Retrieve all license keys for a specific email"""
    try:
        response = supabase.table('license_keys').select('*').eq('email', email).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Supabase error: {response.error}")
            return {"success": False, "error": response.error}
        
        return {"success": True, "data": response.data}
    
    except Exception as e:
        logger.error(f"Error retrieving license keys from Supabase: {str(e)}")
        return {"success": False, "error": str(e)}

async def verify_license_key(license_key: str) -> Dict:
    """Verify if a license key is valid"""
    result = await get_license_key(license_key)
    if not result["success"]:
        return result
    
    is_valid = result["data"]["is_active"]
    return {
        "success": True, 
        "is_valid": is_valid, 
        "data": result["data"]
    }
