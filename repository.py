from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, date
from models import Location, APIKey
import json
import bcrypt


class LocationRepository:
    """Data access layer for locations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, latitude: float, longitude: float, timestamp: datetime, **kwargs) -> Location:
        """Create a new location record"""
        location = Location(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            altitude=kwargs.get("altitude"),
            accuracy=kwargs.get("accuracy"),
            device_id=kwargs.get("device_id"),
            tracker_id=kwargs.get("tracker_id"),
            battery=kwargs.get("battery"),
            connection=kwargs.get("connection"),
            user_id=kwargs.get("user_id"),
            raw_data=json.dumps(kwargs) if kwargs else None,
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def get_all(self, limit: int = None, offset: int = 0):
        """Get all locations with optional pagination"""
        query = self.db.query(Location).order_by(desc(Location.server_received_at))
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    def get_by_date(self, target_date: date):
        """Get all locations for a specific date"""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        return self.db.query(Location).filter(
            and_(
                Location.server_received_at >= start_datetime,
                Location.server_received_at <= end_datetime
            )
        ).order_by(Location.server_received_at).all()

    def get_by_device(self, device_id: str):
        """Get all locations for a specific device"""
        return self.db.query(Location).filter(
            Location.device_id == device_id
        ).order_by(desc(Location.server_received_at)).all()

    def count(self) -> int:
        """Get total location count"""
        return self.db.query(Location).count()


class APIKeyRepository:
    """Data access layer for API keys"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, key_hash: str, key_prefix: str, user_name: str, description: str = None, expires_at = None) -> APIKey:
        """
        Create a new API key.
        
        Args:
            key_hash: bcrypt hash of the plaintext key
            key_prefix: First 8 characters of plaintext key (for indexed lookups)
            user_name: Username to associate with the key
            description: Optional key description
            expires_at: Optional expiration datetime
        """
        api_key = APIKey(
            key_prefix=key_prefix,
            key_hash=key_hash,
            user_name=user_name,
            description=description,
            expires_at=expires_at
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def get_by_key_hash(self, plaintext_key: str) -> APIKey:
        """
        Get API key by comparing plaintext key against bcrypt hashes.
        
        Queries by key_prefix first (indexed), then verifies full hash.
        
        Args:
            plaintext_key: The plaintext API key from the request
            
        Returns:
            APIKey record if found and hash matches, None otherwise
        """
        if not plaintext_key or len(plaintext_key) < 8:
            return None
        
        # Get first 8 characters as prefix
        key_prefix = plaintext_key[:8]
        
        # Query by prefix (indexed for performance)
        candidate_keys = self.db.query(APIKey).filter(
            and_(
                APIKey.key_prefix == key_prefix,
                APIKey.is_active == 1
            )
        ).all()
        
        # Verify the full plaintext key against each candidate's bcrypt hash
        for key_record in candidate_keys:
            try:
                if bcrypt.checkpw(plaintext_key.encode(), key_record.key_hash.encode()):
                    return key_record
            except Exception:
                # Invalid hash format, skip this record
                continue
        
        return None

    def get_by_user(self, user_name: str):
        """Get all active API keys for a user"""
        return self.db.query(APIKey).filter(
            and_(APIKey.user_name == user_name, APIKey.is_active == 1)
        ).all()

    def update_last_used(self, key_id: int) -> None:
        """Update the last_used timestamp for a key"""
        key_record = self.db.query(APIKey).filter(APIKey.id == key_id).first()
        if key_record:
            key_record.last_used = datetime.utcnow()
            self.db.commit()

    def revoke(self, key_id: int) -> bool:
        """
        Revoke an API key by marking it inactive.
        
        Args:
            key_id: The ID of the key to revoke
            
        Returns:
            True if revoked successfully, False if not found
        """
        api_key = self.db.query(APIKey).filter(APIKey.id == key_id).first()
        if api_key:
            api_key.is_active = 0
            self.db.commit()
            return True
        return False
        return False

    def update_last_used(self, key: str):
        """Update last used timestamp for an API key"""
        api_key = self.db.query(APIKey).filter(APIKey.key == key).first()
        if api_key:
            api_key.last_used = datetime.utcnow()
            self.db.commit()
