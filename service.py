from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import hashlib
import bcrypt
import secrets
from repository import LocationRepository, APIKeyRepository
from config import Config
import logging

logger = logging.getLogger(__name__)


class LocationService:
    """Business logic for location handling"""

    def __init__(self, db: Session):
        self.location_repo = LocationRepository(db)
        self.db = db

    def ingest_location(self, data: dict):
        """Process incoming OwnTracks location data"""
        # Extract OwnTracks fields
        tst = data.get("tst")
        if tst:
            timestamp = datetime.fromtimestamp(tst)
        else:
            timestamp = datetime.utcnow()

        location = self.location_repo.create(
            latitude=data.get("lat"),
            longitude=data.get("lon"),
            timestamp=timestamp,
            altitude=data.get("alt"),
            accuracy=data.get("acc"),
            device_id=data.get("devid", data.get("deviceId")),
            tracker_id=data.get("tid"),
            battery=data.get("batt"),
            connection=data.get("conn"),
            user_id=data.get("user"),
            **data  # Store all extra fields
        )
        return location

    def get_history(self, limit: int = None, offset: int = 0):
        """Get location history with pagination"""
        locations = self.location_repo.get_all(limit=limit, offset=offset)
        total = self.location_repo.count()
        return {"total": total, "data": locations}

    def get_history_by_date(self, target_date: date):
        """Get locations for a specific date"""
        locations = self.location_repo.get_by_date(target_date)
        return {"date": target_date.isoformat(), "count": len(locations), "data": locations}

    def get_device_history(self, device_id: str):
        """Get all locations for a device"""
        locations = self.location_repo.get_by_device(device_id)
        return {"device_id": device_id, "count": len(locations), "data": locations}


class APIKeyService:
    """Business logic for API key management"""

    def __init__(self, db: Session):
        self.api_key_repo = APIKeyRepository(db)
        self.db = db

    def generate_api_key(self, user_name: str, description: str = None) -> dict:
        """
        Generate a new API key for a user.
        
        Returns the plaintext key ONLY at creation time.
        The key cannot be recovered after this - users must save it immediately.
        
        Args:
            user_name: Username to associate with the key (alphanumeric, 1-255 chars)
            description: Optional description of the key's purpose
            
        Returns:
            Dictionary with plaintext api_key, user, created_at, and expires_at
        """
        # Validate user_name
        if not user_name or not isinstance(user_name, str):
            raise ValueError("user_name must be a non-empty string")
        if len(user_name) < 1 or len(user_name) > 255:
            raise ValueError("user_name must be 1-255 characters")
        if not user_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError("user_name must contain only alphanumeric characters, hyphens, and underscores")
        
        # Validate description if provided
        if description and len(description) > 1000:
            raise ValueError("description must be 1000 characters or less")
        
        # Generate cryptographically secure random token
        plaintext_key = secrets.token_urlsafe(32)  # ~43 characters
        
        # Extract prefix before hashing (for indexed lookups)
        key_prefix = plaintext_key[:8]
        
        # Hash with bcrypt
        key_hash = bcrypt.hashpw(plaintext_key.encode(), bcrypt.gensalt(rounds=12)).decode()
        
        # Calculate expiration if configured
        expires_at = None
        if Config.API_KEY_EXPIRATION_DAYS > 0:
            expires_at = datetime.utcnow() + timedelta(days=Config.API_KEY_EXPIRATION_DAYS)
        
        created_key = self.api_key_repo.create(
            key_hash=key_hash,
            key_prefix=key_prefix,
            user_name=user_name,
            description=description,
            expires_at=expires_at
        )
        
        logger.info(f"API key generated for user: {user_name}")
        
        return {
            "api_key": plaintext_key,  # Show only at creation time!
            "user": user_name,
            "created_at": created_key.created_at.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "warning": "⚠️  Save this key now. You will not be able to view it again."
        }

    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify if an API key is valid.
        Checks: key hash matches, is active, and not expired.
        
        Args:
            api_key: The plaintext API key to verify
            
        Returns:
            True if valid and active, False otherwise
        """
        if not api_key:
            return False
        
        try:
            key_record = self.api_key_repo.get_by_key_hash(api_key)
            
            if not key_record:
                return False
            
            # Check if revoked
            if key_record.is_active != 1:
                return False
            
            # Check if expired
            if key_record.expires_at and datetime.utcnow() > key_record.expires_at:
                logger.warning(f"API key expired for user: {key_record.user_name}")
                return False
            
            # Update last_used timestamp
            self.api_key_repo.update_last_used(key_record.id)
            
            return True
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return False

    def get_api_key_info(self, api_key: str) -> dict:
        """
        Get info about an API key without exposing the hash.
        
        Args:
            api_key: The plaintext API key
            
        Returns:
            Dictionary with user, created_at, expires_at, last_used, or None if not found
        """
        try:
            key_record = self.api_key_repo.get_by_key_hash(api_key)
            if key_record and key_record.is_active == 1:
                expires_in = None
                if key_record.expires_at:
                    expires_in = (key_record.expires_at - datetime.utcnow()).days
                
                return {
                    "user": key_record.user_name,
                    "created_at": key_record.created_at.isoformat(),
                    "expires_at": key_record.expires_at.isoformat() if key_record.expires_at else None,
                    "expires_in_days": expires_in,
                    "last_used": key_record.last_used.isoformat() if key_record.last_used else None
                }
        except Exception as e:
            logger.error(f"Error getting API key info: {e}")
        
        return None

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key by marking it inactive.
        
        Args:
            api_key: The plaintext API key to revoke
            
        Returns:
            True if revoked successfully, False if not found
        """
        try:
            key_record = self.api_key_repo.get_by_key_hash(api_key)
            if key_record:
                success = self.api_key_repo.revoke(key_record.id)
                if success:
                    logger.info(f"API key revoked for user: {key_record.user_name}")
                return success
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
        
        return False
        return self.api_key_repo.revoke(api_key)
