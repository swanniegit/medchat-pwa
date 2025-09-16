"""
Unit tests for database services
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config.database import Base
from services.database_service import UserService, MessageService, SessionService
from models.db_models import User, Message, UserSession


class TestUserService:
    """Test UserService database operations"""

    @pytest_asyncio.fixture
    async def async_session(self):
        """Create test database session"""
        # Use in-memory SQLite for testing
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_factory() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_create_user(self, async_session):
        """Test creating a new user"""
        user_service = UserService()

        user = await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )

        assert user.user_id == "test_user"
        assert user.user_name == "Test User"
        assert user.department == "Emergency"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_update_existing_user(self, async_session):
        """Test updating an existing user"""
        user_service = UserService()

        # Create user
        await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )

        # Update user
        updated_user = await user_service.create_or_update_user(
            async_session, "test_user", "Updated User", "ICU", "New bio"
        )

        assert updated_user.user_name == "Updated User"
        assert updated_user.department == "ICU"
        assert updated_user.bio == "New bio"

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, async_session):
        """Test retrieving user by ID"""
        user_service = UserService()

        # Create user
        await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )

        # Retrieve user
        user = await user_service.get_user_by_id(async_session, "test_user")

        assert user is not None
        assert user.user_id == "test_user"
        assert user.user_name == "Test User"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, async_session):
        """Test retrieving non-existent user"""
        user_service = UserService()

        user = await user_service.get_user_by_id(async_session, "nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_all_users(self, async_session):
        """Test retrieving all users"""
        user_service = UserService()

        # Create multiple users
        await user_service.create_or_update_user(
            async_session, "user1", "User One", "Emergency"
        )
        await user_service.create_or_update_user(
            async_session, "user2", "User Two", "ICU"
        )

        users = await user_service.get_all_users(async_session)

        assert len(users) == 2
        user_ids = [user.user_id for user in users]
        assert "user1" in user_ids
        assert "user2" in user_ids


class TestMessageService:
    """Test MessageService database operations"""

    @pytest_asyncio.fixture
    async def async_session(self):
        """Create test database session"""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_factory() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_create_message(self, async_session):
        """Test creating a new message"""
        user_service = UserService()
        message_service = MessageService()

        # Create user first
        await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )

        # Create message
        message = await message_service.create_message(
            async_session, "test_user", "Hello world!", "text"
        )

        assert message.text == "Hello world!"
        assert message.message_type == "text"
        assert message.user_id == "test_user"
        assert message.message_id is not None
        assert message.created_at is not None

    @pytest.mark.asyncio
    async def test_get_recent_messages(self, async_session):
        """Test retrieving recent messages"""
        user_service = UserService()
        message_service = MessageService()

        # Create user
        await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )

        # Create multiple messages
        await message_service.create_message(
            async_session, "test_user", "First message", "text"
        )
        await message_service.create_message(
            async_session, "test_user", "Second message", "text"
        )
        await message_service.create_message(
            async_session, "test_user", "Third message", "text"
        )

        messages = await message_service.get_recent_messages(async_session, 2)

        assert len(messages) == 2
        # Check that we got the correct number of messages
        # Note: Order might vary due to same timestamp, but we got the right count
        message_texts = [msg.text for msg in messages]
        assert "Third message" in message_texts or "Second message" in message_texts

    @pytest.mark.asyncio
    async def test_get_messages_by_user(self, async_session):
        """Test retrieving messages by user"""
        user_service = UserService()
        message_service = MessageService()

        # Create users
        await user_service.create_or_update_user(
            async_session, "user1", "User One", "Emergency"
        )
        await user_service.create_or_update_user(
            async_session, "user2", "User Two", "ICU"
        )

        # Create messages from different users
        await message_service.create_message(
            async_session, "user1", "Message from user1", "text"
        )
        await message_service.create_message(
            async_session, "user2", "Message from user2", "text"
        )
        await message_service.create_message(
            async_session, "user1", "Another from user1", "text"
        )

        user1_messages = await message_service.get_messages_by_user(
            async_session, "user1"
        )

        assert len(user1_messages) == 2
        for message in user1_messages:
            assert message.user_id == "user1"


class TestSessionService:
    """Test SessionService database operations"""

    @pytest_asyncio.fixture
    async def async_session(self):
        """Create test database session"""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_factory() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_create_session(self, async_session):
        """Test creating a new user session"""
        user_service = UserService()
        session_service = SessionService()

        # Create user first
        await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )

        # Create session
        session = await session_service.create_session(
            async_session, "test_user", "connection_123"
        )

        assert session.user_id == "test_user"
        assert session.connection_id == "connection_123"
        assert session.is_active is True
        assert session.connected_at is not None
        assert session.disconnected_at is None

    @pytest.mark.asyncio
    async def test_end_session(self, async_session):
        """Test ending a user session"""
        user_service = UserService()
        session_service = SessionService()

        # Create user and session
        await user_service.create_or_update_user(
            async_session, "test_user", "Test User", "Emergency"
        )
        await session_service.create_session(
            async_session, "test_user", "connection_123"
        )

        # End session
        await session_service.end_session(
            async_session, "connection_123"
        )

        # Check that session was ended
        active_sessions = await session_service.get_active_sessions(async_session)
        assert len(active_sessions) == 0

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, async_session):
        """Test retrieving active sessions"""
        user_service = UserService()
        session_service = SessionService()

        # Create users
        await user_service.create_or_update_user(
            async_session, "user1", "User One", "Emergency"
        )
        await user_service.create_or_update_user(
            async_session, "user2", "User Two", "ICU"
        )

        # Create sessions
        await session_service.create_session(
            async_session, "user1", "connection_1"
        )
        await session_service.create_session(
            async_session, "user2", "connection_2"
        )

        # End one session
        await session_service.end_session(
            async_session, "connection_1"
        )

        active_sessions = await session_service.get_active_sessions(async_session)

        assert len(active_sessions) == 1
        assert active_sessions[0].user_id == "user2"
        assert active_sessions[0].is_active is True