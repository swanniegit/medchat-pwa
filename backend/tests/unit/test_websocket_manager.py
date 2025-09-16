import pytest
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from services.websocket_manager import ConnectionManager


class TestConnectionManager:

    def setup_method(self):
        """Create a fresh ConnectionManager for each test"""
        self.manager = ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test connecting a WebSocket"""
        mock_websocket = AsyncMock()
        user_id = "test_user"

        await self.manager.connect(mock_websocket, user_id)

        # Verify websocket.accept() was called
        mock_websocket.accept.assert_called_once()

        # Verify user was added to active connections
        assert user_id in self.manager.active_connections
        assert self.manager.active_connections[user_id] == mock_websocket

    def test_disconnect_user(self):
        """Test disconnecting a user"""
        user_id = "test_user"
        mock_websocket = Mock()

        # Add user manually
        self.manager.active_connections[user_id] = mock_websocket
        self.manager.users[user_id] = {"name": "Test User"}

        # Disconnect
        self.manager.disconnect(user_id)

        # Verify user was removed
        assert user_id not in self.manager.active_connections
        assert user_id not in self.manager.users

    def test_disconnect_nonexistent_user(self):
        """Test disconnecting a user that doesn't exist"""
        # Should not raise an error
        self.manager.disconnect("nonexistent_user")

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending a personal message"""
        user_id = "test_user"
        message = "Hello, test user!"
        mock_websocket = AsyncMock()

        # Add user to connections
        self.manager.active_connections[user_id] = mock_websocket

        await self.manager.send_personal_message(message, user_id)

        # Verify message was sent
        mock_websocket.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_to_nonexistent_user(self):
        """Test sending message to non-existent user"""
        await self.manager.send_personal_message("Hello", "nonexistent_user")
        # Should not raise an error

    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting a message to all users"""
        message = "Broadcast message"
        users = ["user1", "user2", "user3"]
        mock_websockets = {}

        # Add multiple users
        for user_id in users:
            mock_websocket = AsyncMock()
            mock_websockets[user_id] = mock_websocket
            self.manager.active_connections[user_id] = mock_websocket

        await self.manager.broadcast(message)

        # Verify all users received the message
        for mock_websocket in mock_websockets.values():
            mock_websocket.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_message_exclude_user(self):
        """Test broadcasting with user exclusion"""
        message = "Broadcast message"
        users = ["user1", "user2", "user3"]
        excluded_user = "user2"
        mock_websockets = {}

        # Add multiple users
        for user_id in users:
            mock_websocket = AsyncMock()
            mock_websockets[user_id] = mock_websocket
            self.manager.active_connections[user_id] = mock_websocket

        await self.manager.broadcast(message, exclude_user=excluded_user)

        # Verify excluded user did not receive message
        mock_websockets[excluded_user].send_text.assert_not_called()

        # Verify other users received the message
        for user_id, mock_websocket in mock_websockets.items():
            if user_id != excluded_user:
                mock_websocket.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_connection_error(self):
        """Test broadcast handling connection errors gracefully"""
        message = "Broadcast message"
        users = ["user1", "user2"]

        # Create one working websocket and one that raises an exception
        working_websocket = AsyncMock()
        failing_websocket = AsyncMock()
        failing_websocket.send_text.side_effect = Exception("Connection lost")

        self.manager.active_connections["user1"] = working_websocket
        self.manager.active_connections["user2"] = failing_websocket

        # Should not raise an exception
        await self.manager.broadcast(message)

        # Working websocket should still receive the message
        working_websocket.send_text.assert_called_once_with(message)
        failing_websocket.send_text.assert_called_once_with(message)

    def test_get_online_users(self):
        """Test getting online users"""
        users = ["user1", "user2", "user3"]

        # Add users
        for user_id in users:
            self.manager.active_connections[user_id] = Mock()

        result = self.manager.get_online_users()

        assert result["count"] == 3
        assert set(result["online_users"]) == set(users)

    def test_get_online_users_empty(self):
        """Test getting online users when none are connected"""
        result = self.manager.get_online_users()

        assert result["count"] == 0
        assert result["online_users"] == []

    def test_get_connection_count(self):
        """Test getting connection count"""
        assert self.manager.get_connection_count() == 0

        # Add some connections
        for i in range(5):
            self.manager.active_connections[f"user{i}"] = Mock()

        assert self.manager.get_connection_count() == 5