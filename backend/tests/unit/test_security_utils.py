import pytest
from datetime import datetime, timedelta
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from security.utils import SecurityUtils, rate_limit_storage


class TestSecurityUtils:

    def setup_method(self):
        """Clear rate limit storage before each test"""
        rate_limit_storage.clear()

    def test_sanitize_input_basic(self):
        """Test basic input sanitization"""
        result = SecurityUtils.sanitize_input("Hello World")
        assert result == "Hello World"

    def test_sanitize_input_html_escape(self):
        """Test HTML escaping"""
        result = SecurityUtils.sanitize_input("<script>alert('xss')</script>")
        # Should escape HTML tags and special characters
        assert "<script>" not in result  # Original tags should be escaped/removed
        assert "</script>" not in result
        # Should not contain actual script content as-is
        assert result != "<script>alert('xss')</script>"

    def test_sanitize_input_length_limit(self):
        """Test length limiting"""
        long_text = "A" * 1500
        result = SecurityUtils.sanitize_input(long_text, max_length=100)
        assert len(result) == 100

    def test_sanitize_input_empty(self):
        """Test empty input handling"""
        result = SecurityUtils.sanitize_input("")
        assert result == ""

        result = SecurityUtils.sanitize_input(None)
        assert result == ""

    def test_validate_user_id_valid(self):
        """Test valid user ID formats"""
        assert SecurityUtils.validate_user_id("user123") == True
        assert SecurityUtils.validate_user_id("test-user") == True
        assert SecurityUtils.validate_user_id("user_name") == True
        assert SecurityUtils.validate_user_id("ABC123xyz") == True

    def test_validate_user_id_invalid(self):
        """Test invalid user ID formats"""
        assert SecurityUtils.validate_user_id("") == False
        assert SecurityUtils.validate_user_id(None) == False
        assert SecurityUtils.validate_user_id("user@domain.com") == False
        assert SecurityUtils.validate_user_id("user with spaces") == False
        assert SecurityUtils.validate_user_id("user!special") == False
        assert SecurityUtils.validate_user_id("A" * 101) == False  # Too long

    def test_validate_message_length_valid(self):
        """Test valid message lengths"""
        assert SecurityUtils.validate_message_length("Hello") == True
        assert SecurityUtils.validate_message_length("A" * 1000) == True  # Max length
        assert SecurityUtils.validate_message_length("A" * 500) == True

    def test_validate_message_length_invalid(self):
        """Test invalid message lengths"""
        assert SecurityUtils.validate_message_length("") == False  # Empty
        assert SecurityUtils.validate_message_length("A" * 1001) == False  # Too long

    def test_hash_password(self):
        """Test password hashing"""
        password = "secure_password123"
        hashed = SecurityUtils.hash_password(password)

        # Should return salt + hash (64 char salt + hash)
        assert len(hashed) > 64
        assert isinstance(hashed, str)

        # Same password should produce different hashes (due to salt)
        hashed2 = SecurityUtils.hash_password(password)
        assert hashed != hashed2

    def test_verify_password(self):
        """Test password verification"""
        password = "secure_password123"
        hashed = SecurityUtils.hash_password(password)

        # Correct password should verify
        assert SecurityUtils.verify_password(hashed, password) == True

        # Wrong password should not verify
        assert SecurityUtils.verify_password(hashed, "wrong_password") == False

    def test_rate_limit_within_limit(self):
        """Test rate limiting within limits"""
        client_id = "test_client"

        # Should allow requests within limit
        for i in range(5):
            result = SecurityUtils.check_rate_limit(client_id, max_requests=10, time_window=60)
            assert result == True

    def test_rate_limit_exceed_limit(self):
        """Test rate limiting when exceeding limits"""
        client_id = "test_client"
        max_requests = 3

        # Fill up the limit
        for i in range(max_requests):
            result = SecurityUtils.check_rate_limit(client_id, max_requests=max_requests, time_window=60)
            assert result == True

        # Next request should be denied
        result = SecurityUtils.check_rate_limit(client_id, max_requests=max_requests, time_window=60)
        assert result == False

    def test_rate_limit_different_clients(self):
        """Test rate limiting for different clients"""
        client1 = "client1"
        client2 = "client2"
        max_requests = 2

        # Both clients should have independent limits
        for i in range(max_requests):
            assert SecurityUtils.check_rate_limit(client1, max_requests=max_requests, time_window=60) == True
            assert SecurityUtils.check_rate_limit(client2, max_requests=max_requests, time_window=60) == True

        # Both should now be at limit
        assert SecurityUtils.check_rate_limit(client1, max_requests=max_requests, time_window=60) == False
        assert SecurityUtils.check_rate_limit(client2, max_requests=max_requests, time_window=60) == False

    def test_rate_limit_cleanup(self):
        """Test that old entries are cleaned up"""
        client_id = "test_client"

        # Manually add old entries to rate_limit_storage
        old_time = datetime.now() - timedelta(seconds=120)  # 2 minutes ago
        rate_limit_storage[client_id] = [old_time, old_time, old_time]

        # Should clean up old entries and allow new requests
        result = SecurityUtils.check_rate_limit(client_id, max_requests=2, time_window=60)
        assert result == True

        # Should only have the new entry now
        assert len(rate_limit_storage[client_id]) == 1