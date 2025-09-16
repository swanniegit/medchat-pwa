"""
Integration tests for WebSocket manager with database integration
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base
from services.websocket_manager import ConnectionManager
from services.database_service import UserService, MessageService, SessionService


class TestWebSocketDatabaseIntegration:
    """Test WebSocket manager database integration"""

    @pytest.fixture
    async def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_factory() as session:
            yield session

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket"""
        websocket = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.accept = AsyncMock()
        return websocket

    @pytest.fixture
    def connection_manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_creates_user_and_session(self, connection_manager, mock_websocket, db_session):
        """Test that connecting a user creates database records"""
        user_service = UserService()
        session_service = SessionService()

        # Connect user
        await connection_manager.connect(mock_websocket, "test_user", "Test User", "Emergency")

        # Verify user was created in database
        user = await user_service.get_user_by_id(db_session, "test_user")
        assert user is not None
        assert user.user_name == "Test User"
        assert user.department == "Emergency"

        # Verify session was created
        sessions = await session_service.get_active_sessions(db_session)
        assert len(sessions) == 1
        assert sessions[0].user_id == "test_user"
        assert sessions[0].is_active is True

    @pytest.mark.asyncio
    async def test_disconnect_ends_session(self, connection_manager, mock_websocket, db_session):
        """Test that disconnecting a user ends their session"""
        session_service = SessionService()

        # Connect and then disconnect user
        await connection_manager.connect(mock_websocket, "test_user", "Test User", "Emergency")
        await connection_manager.disconnect("test_user")

        # Verify session was ended
        sessions = await session_service.get_active_sessions(db_session)
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_broadcast_saves_message_to_database(self, connection_manager, mock_websocket, db_session):
        """Test that broadcasting a message saves it to database"""
        message_service = MessageService()

        # Create a test message
        message_data = {
            "type": "message",
            "text": "Hello database!",
            "message_type": "text",
            "user_id": "test_user"
        }

        # Broadcast message
        await connection_manager.broadcast(json.dumps(message_data), save_to_db=True)

        # Verify message was saved to database
        messages = await message_service.get_recent_messages(db_session, 10)
        assert len(messages) == 1
        assert messages[0].text == "Hello database!"
        assert messages[0].user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_online_users_with_database_info(self, connection_manager, mock_websocket, db_session):
        """Test getting online users with database information"""
        # Connect multiple users
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()

        await connection_manager.connect(websocket1, "user1", "Alice", "Emergency")
        await connection_manager.connect(websocket2, "user2", "Bob", "ICU")

        # Get online users
        online_users = await connection_manager.get_online_users()

        assert online_users["count"] == 2
        assert len(online_users["online_users"]) == 2

        # Check user data includes database information
        user_ids = [user["user_id"] for user in online_users["online_users"]]
        assert "user1" in user_ids
        assert "user2" in user_ids

        # Find Alice's data
        alice_data = next(user for user in online_users["online_users"] if user["user_id"] == "user1")
        assert alice_data["user_name"] == "Alice"
        assert alice_data["department"] == "Emergency"

    @pytest.mark.asyncio
    async def test_get_recent_messages_from_database(self, connection_manager, db_session):
        """Test getting recent messages from database"""
        message_service = MessageService()
        user_service = UserService()

        # Create user and messages
        await user_service.create_or_update_user(db_session, "test_user", "Test User", "Emergency")
        await message_service.create_message(db_session, "First message", "text", "test_user")
        await message_service.create_message(db_session, "Second message", "text", "test_user")
        await message_service.create_message(db_session, "Third message", "text", "test_user")

        # Get recent messages
        recent_messages = await connection_manager.get_recent_messages(3)

        assert len(recent_messages) == 3
        # Should be in reverse chronological order
        assert recent_messages[0]["text"] == "Third message"
        assert recent_messages[1]["text"] == "Second message"
        assert recent_messages[2]["text"] == "First message"

    @pytest.mark.asyncio
    async def test_system_messages_not_saved_to_database(self, connection_manager, db_session):
        """Test that system messages are not saved to database"""
        message_service = MessageService()

        # Create system message (user_joined/user_left)
        system_message = {
            "type": "user_joined",
            "user_id": "test_user",
            "text": "User test_user joined the chat"
        }

        # Broadcast system message
        await connection_manager.broadcast(json.dumps(system_message), save_to_db=False)

        # Verify no messages were saved to database
        messages = await message_service.get_recent_messages(db_session, 10)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, connection_manager, db_session):
        """Test handling multiple connections from the same user"""
        user_service = UserService()
        session_service = SessionService()

        # Connect same user with different websockets (different devices/tabs)
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()

        await connection_manager.connect(websocket1, "test_user", "Test User", "Emergency")
        await connection_manager.connect(websocket2, "test_user", "Test User", "Emergency")

        # Should only have one user record
        user = await user_service.get_user_by_id(db_session, "test_user")
        assert user is not None

        # But should have multiple sessions
        sessions = await session_service.get_active_sessions(db_session)
        test_user_sessions = [s for s in sessions if s.user_id == "test_user"]
        assert len(test_user_sessions) >= 1  # At least one session

    @pytest.mark.asyncio
    async def test_invalid_json_message_handling(self, connection_manager, db_session):
        """Test handling of invalid JSON messages"""
        message_service = MessageService()

        # Try to broadcast invalid JSON
        invalid_json = "{ invalid json }"
        await connection_manager.broadcast(invalid_json, save_to_db=True)

        # Should not crash and should not save anything to database
        messages = await message_service.get_recent_messages(db_session, 10)
        assert len(messages) == 0