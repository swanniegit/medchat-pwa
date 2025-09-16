import re
import hashlib
import secrets
import html
from datetime import datetime
from typing import Dict

# Optional security imports
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, list] = {}

class SecurityUtils:
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not text:
            return ""

        # Limit length
        text = text[:max_length]

        # Remove HTML tags and escape special characters
        if BLEACH_AVAILABLE:
            text = bleach.clean(text, tags=[], strip=True)

        text = html.escape(text)

        return text.strip()

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        if not user_id or len(user_id) > 100:
            return False

        # Only allow alphanumeric, underscore, and hyphen
        return re.match(r'^[a-zA-Z0-9_-]+$', user_id) is not None

    @staticmethod
    def validate_message_length(message: str) -> bool:
        """Validate message length"""
        return 0 < len(message) <= 1000

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt + pwd_hash.hex()

    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        """Verify password against hash"""
        salt = stored_password[:64]
        stored_hash = stored_password[64:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwd_hash.hex() == stored_hash

    @staticmethod
    def check_rate_limit(client_id: str, max_requests: int = 30, time_window: int = 60) -> bool:
        """Simple rate limiting"""
        now = datetime.now()

        if client_id not in rate_limit_storage:
            rate_limit_storage[client_id] = []

        # Clean old entries
        rate_limit_storage[client_id] = [
            timestamp for timestamp in rate_limit_storage[client_id]
            if (now - timestamp).seconds < time_window
        ]

        # Check if limit exceeded
        if len(rate_limit_storage[client_id]) >= max_requests:
            return False

        # Add current request
        rate_limit_storage[client_id].append(now)
        return True