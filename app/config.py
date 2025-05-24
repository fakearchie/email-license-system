from pydantic_settings import BaseSettings
import json

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./license_system.db"
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Shopify settings
    SHOPIFY_WEBHOOK_SECRET: str
    SHOPIFY_SHOP_DOMAIN: str
    
    # Email settings
    SMTP_HOST: str
    SMTP_PORT: int = 465  # Using SSL port for more reliable connections
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    
    # License categories
    LICENSE_CATEGORIES: dict = {
        "basic": {"prefix": "BSC", "validity_days": 365},
        "pro": {"prefix": "PRO", "validity_days": 365},
        "enterprise": {"prefix": "ENT", "validity_days": 365}
    }
    
    # Product category mapping
    PRODUCT_CATEGORY_MAP: dict = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse PRODUCT_CATEGORY_MAP if it's a string
        if isinstance(self.PRODUCT_CATEGORY_MAP, str):
            try:
                self.PRODUCT_CATEGORY_MAP = json.loads(self.PRODUCT_CATEGORY_MAP)
            except json.JSONDecodeError:
                self.PRODUCT_CATEGORY_MAP = {}
    
    class Config:
        env_file = ".env"
