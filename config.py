"""
Configuration and environment variable handling.
Centralizes secret management and validates required environment variables.
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Load and validate configuration from environment variables"""
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Caddyfile configuration
    CADDY_ADMIN_PASSWORD_HASH: str = os.getenv("CADDY_ADMIN_PASSWORD_HASH", "")
    CADDY_OWNTRACKS_PASSWORD_HASH: str = os.getenv("CADDY_OWNTRACKS_PASSWORD_HASH", "")
    
    # API key expiration (in days, 0 = no expiration)
    API_KEY_EXPIRATION_DAYS: int = int(os.getenv("API_KEY_EXPIRATION_DAYS", "365"))
    
    # Log level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        Raises ValueError if required environment variables are missing.
        """
        errors = []
        
        # Check database configuration
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD environment variable is required")
        
        # Build DATABASE_URL if not provided
        if not cls.DATABASE_URL:
            if cls.DB_PASSWORD:
                db_user = os.getenv("DB_USER", "manadia")
                db_host = os.getenv("DB_HOST", "db")
                db_port = os.getenv("DB_PORT", "5432")
                db_name = os.getenv("DB_NAME", "manadia")
                cls.DATABASE_URL = f"postgresql://{db_user}:{cls.DB_PASSWORD}@{db_host}:{db_port}/{db_name}"
            else:
                errors.append("DATABASE_URL or DB_PASSWORD environment variable is required")
        
        # Check Caddy configuration (optional if using different auth method)
        # These are loaded but not strictly required if auth is disabled
        logger.info("Configuration validation: Caddyfile hashes will be loaded from environment")
        
        if errors:
            for error in errors:
                logger.critical(f"Configuration Error: {error}")
            raise ValueError(f"Missing required environment variables: {'; '.join(errors)}")
        
        logger.info("✓ Configuration validation passed")
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database URL, ensuring no credentials are logged"""
        return cls.DATABASE_URL.replace(cls.DB_PASSWORD, "***") if cls.DB_PASSWORD in cls.DATABASE_URL else cls.DATABASE_URL


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Fatal configuration error: {e}")
    raise
