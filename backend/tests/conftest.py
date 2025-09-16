"""
Pytest configuration file with shared fixtures and test setup.
"""
import pytest
import sys
import os
from datetime import datetime

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

# Import modules for testing
from security.utils import rate_limit_storage
from services.websocket_manager import ConnectionManager


@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Automatically reset global state before each test.
    This ensures tests don't interfere with each other.
    """
    # Clear rate limiting storage
    rate_limit_storage.clear()

    yield

    # Clean up after test if needed
    rate_limit_storage.clear()


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing"""
    return {
        "user_id": "test_user_123",
        "user_name": "Dr. Test",
        "department": "Emergency",
        "bio": "Emergency medicine physician"
    }


@pytest.fixture
def sample_message_data():
    """Provide sample message data for testing"""
    return {
        "text": "This is a test message",
        "user_id": "test_user_123",
        "user_name": "Dr. Test",
        "department": "Emergency",
        "bio": "Emergency medicine physician",
        "type": "message"
    }


@pytest.fixture
def connection_manager():
    """Provide a fresh ConnectionManager instance for testing"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Provide a mock WebSocket for testing"""
    from unittest.mock import AsyncMock

    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()

    return websocket


@pytest.fixture
def multiple_users():
    """Provide multiple user data for testing"""
    return [
        {
            "user_id": "doctor1",
            "user_name": "Dr. Smith",
            "department": "Cardiology"
        },
        {
            "user_id": "nurse1",
            "user_name": "Nurse Johnson",
            "department": "ICU"
        },
        {
            "user_id": "admin1",
            "user_name": "Admin Davis",
            "department": "Administration"
        }
    ]


@pytest.fixture
def system_message_data():
    """Provide system message data for testing"""
    return {
        "type": "user_joined",
        "user_id": "test_user",
        "timestamp": datetime.now().isoformat(),
        "message": "User test_user joined the chat"
    }


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)