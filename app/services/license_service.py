from typing import Optional, List, Dict
import logging
import uuid
import os
import json
from app.config import Settings
from app.services import supabase_service

settings = Settings()
logger = logging.getLogger(__name__)

LICENSES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../licenses.json')

async def get_product_category(product_id: str) -> str:
    """Determine license category based on product ID"""
    category_map = settings.PRODUCT_CATEGORY_MAP
    if not category_map or product_id not in category_map:
        # Use simple product ID based logic as fallback
        if product_id.endswith('1'):
            category = "basic"
        elif product_id.endswith('2'):
            category = "pro"
        else:
            category = "enterprise"
        logger.info(f"Using fallback category mapping: {category}")
        return category
    
    category = category_map.get(product_id, "basic")
    logger.info(f"Mapped product {product_id} to category: {category}")
    return category

async def generate_license_key(category: str, order_id: str, product_id: str) -> str:
    """Pop and return the next license key from licenses.json for the given category."""
    try:
        if not os.path.exists(LICENSES_FILE):
            logger.error(f"licenses.json file not found at {LICENSES_FILE}")
            raise Exception("License key file missing. Please contact support.")
        with open(LICENSES_FILE, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse licenses.json: {e}")
                raise Exception("License key file is corrupted. Please contact support.")
            keys = data.get(category, [])
            if not keys:
                logger.error(f"No license keys left for category: {category}")
                raise Exception(f"No license keys left for category: {category}")
            license_key = keys.pop(0)
            data[category] = keys
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
        logger.info(f"Popped license key {license_key} from category {category}")
        return license_key
    except Exception as e:
        logger.error(f"Error retrieving license key: {e}")
        raise

async def store_license_key(
    license_key: str, 
    category: str, 
    email: str, 
    order_id: str, 
    product_id: str,
    product_name: str
) -> Dict:
    """Store a generated license key in Supabase"""
    return await supabase_service.store_license_key(
        license_key=license_key,
        category=category,
        email=email,
        order_id=order_id,
        product_id=product_id,
        product_name=product_name
    )

async def verify_license_key(license_key: str) -> Dict:
    """Verify if a license key is valid"""
    return await supabase_service.verify_license_key(license_key)
        
    with open(get_license_file(category), 'w') as f:
        json.dump(keys, f, indent=2)

async def get_and_remove_license_key(product_id: str) -> Optional[str]:
    """Get and remove a license key for a product"""
    category = get_product_category(product_id)
    
    if IS_VERCEL:
        # In Vercel, generate a key instead of loading from file
        order_id = "VERCEL"  # This would normally come from the order
        return f"{category.upper()}-{order_id}-{product_id[-4:]}"

    keys = load_licenses(category)
    
    if not keys:
        raise Exception(f"No license keys available for category: {category}")
    
    # Get and remove first available key
    key = keys.pop(0)
    save_licenses(category, keys)
    return key

def import_keys(category: str, new_keys: List[str]) -> None:
    """Import new license keys for a category"""
    if IS_VERCEL:
        logger.info(f"Running in Vercel, skipping import for {category}")
        return
        
    keys = load_licenses(category)
    # Add only unique keys
    keys.extend([key for key in new_keys if key not in keys])
    save_licenses(category, keys)

def get_available_count(category: str) -> int:
    """Get count of available licenses for a category"""
    if IS_VERCEL:
        return 999  # Mock unlimited keys in Vercel
        
    return len(load_licenses(category))

def list_available_keys(category: str) -> List[str]:
    """List all available license keys for a category"""
    return load_licenses(category)

def remove_key(key: str) -> bool:
    """Remove a specific license key from all categories"""
    if IS_VERCEL:
        logger.info(f"Running in Vercel, skipping key removal for {key}")
        return True
        
    for category in ["basic", "pro", "enterprise"]:
        keys = load_licenses(category)
        if key in keys:
            keys.remove(key)
            save_licenses(category, keys)
            return True
    return False

async def pop_license_key(category: str) -> str:
    """Pop and return the next license key from licenses.json for the given category."""
    try:
        if not os.path.exists(LICENSES_FILE):
            logger.error(f"licenses.json file not found at {LICENSES_FILE}")
            raise Exception("License key file missing. Please contact support.")
        with open(LICENSES_FILE, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse licenses.json: {e}")
                raise Exception("License key file is corrupted. Please contact support.")
            keys = data.get(category, [])
            if not keys:
                logger.error(f"No license keys left for category: {category}")
                raise Exception(f"No license keys left for category: {category}")
            license_key = keys.pop(0)
            data[category] = keys
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
        logger.info(f"Popped license key {license_key} from category {category}")
        return license_key
    except Exception as e:
        logger.error(f"Error retrieving license key: {e}")
        raise

async def add_licenses(category: str, new_keys: list[str]):
    """Add new license keys to a category in licenses.json."""
    try:
        if not os.path.exists(LICENSES_FILE):
            data = {}
        else:
            with open(LICENSES_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        keys = data.get(category, [])
        # Add only unique keys
        keys.extend([key for key in new_keys if key not in keys])
        data[category] = keys
        with open(LICENSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Added {len(new_keys)} license keys to category {category}")
    except Exception as e:
        logger.error(f"Error adding licenses: {e}")
        raise
