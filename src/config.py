"""
Configuration management for ParkM Zoho integration
"""
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Zoho Desk Configuration
    zoho_org_id: str
    zoho_data_center: str = "com"
    zoho_base_url: str = ""
    
    # Authentication (either OAuth or API Token)
    zoho_api_token: str | None = None
    zoho_client_id: str | None = None
    zoho_client_secret: str | None = None
    zoho_redirect_uri: str | None = None
    zoho_refresh_token: str | None = None
    
    # AI Configuration
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_provider: str = "openai"  # or "anthropic"
    ai_model: str = "gpt-4o-mini"  # or "claude-3-5-sonnet-20241022"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    debug: bool = True
    
    # Database (optional for analytics)
    database_url: str | None = None
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-construct base URL if not provided
        if not self.zoho_base_url:
            self.zoho_base_url = f"https://desk.zoho.{self.zoho_data_center}/api/v1"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
