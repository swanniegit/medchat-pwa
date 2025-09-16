import pytest
from datetime import datetime
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from models.message import MessageModel
from models.user import UserModel, UserProfile


class TestMessageModel:

    def test_create_basic_message(self):
        """Test creating a basic message"""
        message = MessageModel(
            text="Hello, world!",
            user_id="test_user",
            user_name="Test User",
            department="Emergency"
        )

        assert message.text == "Hello, world!"
        assert message.user_id == "test_user"
        assert message.user_name == "Test User"
        assert message.department == "Emergency"
        assert message.type == "message"  # default value

    def test_create_message_with_optional_fields(self):
        """Test creating message with all optional fields"""
        timestamp = datetime.now().isoformat()
        message = MessageModel(
            text="Test message",
            user_id="user123",
            user_name="John Doe",
            department="ICU",
            bio="Emergency physician",
            timestamp=timestamp,
            message_id="msg_123",
            type="notification"
        )

        assert message.text == "Test message"
        assert message.bio == "Emergency physician"
        assert message.timestamp == timestamp
        assert message.message_id == "msg_123"
        assert message.type == "notification"

    def test_create_system_message(self):
        """Test creating system message"""
        system_msg = MessageModel.create_system_message(
            "user_joined",
            "user123",
            "User has joined the chat"
        )

        assert system_msg["type"] == "user_joined"
        assert system_msg["user_id"] == "user123"
        assert system_msg["message"] == "User has joined the chat"
        assert "timestamp" in system_msg

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(system_msg["timestamp"])

    def test_add_server_metadata(self):
        """Test adding server metadata to message"""
        message = MessageModel(
            text="Test message",
            user_id="user123"
        )

        # Initially no metadata
        assert message.timestamp is None
        assert message.message_id is None

        # Add metadata
        updated_message = message.add_server_metadata()

        # Should have metadata now
        assert updated_message.timestamp is not None
        assert updated_message.message_id is not None

        # Verify timestamp is valid
        datetime.fromisoformat(updated_message.timestamp)

        # Verify message_id is not empty
        assert len(updated_message.message_id) > 0

    def test_message_model_validation(self):
        """Test that required fields are validated"""
        # Should work with minimal required fields
        message = MessageModel(text="Hello", user_id="user123")
        assert message.text == "Hello"
        assert message.user_id == "user123"

        # Test with empty text - should work (validation happens elsewhere)
        message = MessageModel(text="", user_id="user123")
        assert message.text == ""


class TestUserModel:

    def test_create_basic_user(self):
        """Test creating a basic user"""
        user = UserModel(user_id="user123")

        assert user.user_id == "user123"
        assert user.user_name is None
        assert user.department is None
        assert user.bio is None

    def test_create_complete_user(self):
        """Test creating user with all fields"""
        user = UserModel(
            user_id="user123",
            user_name="Dr. Smith",
            department="Cardiology",
            bio="Cardiologist with 10 years experience"
        )

        assert user.user_id == "user123"
        assert user.user_name == "Dr. Smith"
        assert user.department == "Cardiology"
        assert user.bio == "Cardiologist with 10 years experience"

    def test_user_model_validation(self):
        """Test user model validation"""
        # user_id is required
        user = UserModel(user_id="test_user")
        assert user.user_id == "test_user"


class TestUserProfile:

    def test_create_basic_profile(self):
        """Test creating a basic user profile"""
        profile = UserProfile(
            user_id="user123",
            user_name="Dr. Johnson",
            department="Emergency"
        )

        assert profile.user_id == "user123"
        assert profile.user_name == "Dr. Johnson"
        assert profile.department == "Emergency"
        assert profile.status == "online"  # default value

    def test_create_complete_profile(self):
        """Test creating complete user profile"""
        profile = UserProfile(
            user_id="user456",
            user_name="Dr. Williams",
            department="ICU",
            bio="Critical care specialist",
            status="busy"
        )

        assert profile.user_id == "user456"
        assert profile.user_name == "Dr. Williams"
        assert profile.department == "ICU"
        assert profile.bio == "Critical care specialist"
        assert profile.status == "busy"

    def test_profile_required_fields(self):
        """Test that required fields are enforced"""
        # All of user_id, user_name, department are required for UserProfile
        profile = UserProfile(
            user_id="user789",
            user_name="Dr. Brown",
            department="Surgery"
        )

        assert profile.user_id == "user789"
        assert profile.user_name == "Dr. Brown"
        assert profile.department == "Surgery"


class TestModelInteraction:

    def test_message_with_user_data(self):
        """Test creating message with user model data"""
        user = UserModel(
            user_id="user123",
            user_name="Dr. Adams",
            department="Neurology",
            bio="Neurologist specializing in stroke care"
        )

        message = MessageModel(
            text="Patient needs immediate attention",
            user_id=user.user_id,
            user_name=user.user_name,
            department=user.department,
            bio=user.bio
        )

        assert message.user_id == user.user_id
        assert message.user_name == user.user_name
        assert message.department == user.department
        assert message.bio == user.bio

    def test_profile_from_user(self):
        """Test creating profile from user data"""
        user = UserModel(
            user_id="user456",
            user_name="Dr. Taylor",
            department="Pediatrics",
            bio="Pediatric emergency medicine"
        )

        profile = UserProfile(
            user_id=user.user_id,
            user_name=user.user_name or "Unknown",
            department=user.department or "Unknown",
            bio=user.bio,
            status="available"
        )

        assert profile.user_id == user.user_id
        assert profile.user_name == user.user_name
        assert profile.department == user.department
        assert profile.bio == user.bio
        assert profile.status == "available"