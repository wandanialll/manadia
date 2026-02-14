"""
Audit logging for administrative operations.
Tracks API key generation, revocation, and other sensitive actions.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditLog:
    """
    Audit logging functionality for tracking administrative operations.
    Can log to file, database, or both.
    """
    
    # Action types
    ACTION_API_KEY_GENERATED = "api_key_generated"
    ACTION_API_KEY_REVOKED = "api_key_revoked"
    ACTION_API_KEY_VERIFIED = "api_key_verified"
    
    @staticmethod
    def log_action(
        action: str,
        user: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
        db: Optional[Session] = None
    ) -> None:
        """
        Log an administrative action.
        
        Args:
            action: Type of action (e.g., api_key_generated)
            user: Username or identifier performing the action
            details: Additional context about the action (e.g., api_key_id, description)
            status: "success" or "failure"
            ip_address: Client IP address if available
            db: Database session for persistent logging (optional)
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "user": user,
            "status": status,
            "details": details or {},
            "ip_address": ip_address
        }
        
        # Log to file/stdout with INFO level for success, WARNING for failures
        log_level = logging.INFO if status == "success" else logging.WARNING
        logger.log(log_level, f"AUDIT: {json.dumps(log_entry)}")
        
        # Optionally persist to database (future enhancement)
        # if db:
        #     audit_db_entry = AuditLogEntry(**log_entry)
        #     db.add(audit_db_entry)
        #     db.commit()


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from FastAPI request, accounting for proxies"""
    if request:
        # Check X-Forwarded-For header (from reverse proxy like Caddy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
    
    return None
