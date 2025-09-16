from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime

from models.db_models import User, Message, UserSession
from models.message import MessageModel  # Keep Pydantic for validation
from models.user import UserModel

class UserService:
    """Service for user database operations"""

    @staticmethod
    async def create_or_update_user(
        db: AsyncSession,
        user_id: str,
        user_name: str,
        department: str,
        bio: str = None
    ) -> User:
        """Create a new user or update existing user information"""
        # Check if user exists
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            # Update existing user
            user.user_name = user_name
            user.department = department
            user.bio = bio
            user.last_seen = datetime.utcnow()
        else:
            # Create new user
            user = User(
                user_id=user_id,
                user_name=user_name,
                department=department,
                bio=bio,
                last_seen=datetime.utcnow()
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_users(db: AsyncSession) -> List[User]:
        """Get all active users"""
        result = await db.execute(select(User).where(User.is_active == True))
        return result.scalars().all()

    @staticmethod
    async def update_last_seen(db: AsyncSession, user_id: str):
        """Update user's last seen timestamp"""
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(last_seen=datetime.utcnow())
        )
        await db.commit()

class MessageService:
    """Service for message database operations"""

    @staticmethod
    async def create_message(
        db: AsyncSession,
        user_id: str,
        text: str,
        message_type: str = "message"
    ) -> Message:
        """Create a new message"""
        message = Message(
            message_id=str(uuid.uuid4()),
            text=text,
            message_type=message_type,
            user_id=user_id
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # Load user relationship
        await db.refresh(message, ["user"])
        return message

    @staticmethod
    async def get_recent_messages(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """Get recent messages with user information"""
        result = await db.execute(
            select(Message)
            .options(selectinload(Message.user))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_messages_by_user(
        db: AsyncSession,
        user_id: str,
        limit: int = 50
    ) -> List[Message]:
        """Get messages by specific user"""
        result = await db.execute(
            select(Message)
            .options(selectinload(Message.user))
            .where(Message.user_id == user_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_message_count(db: AsyncSession) -> int:
        """Get total message count"""
        result = await db.execute(select(func.count(Message.id)))
        return result.scalar()

class SessionService:
    """Service for user session management"""

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: str,
        connection_id: str
    ) -> UserSession:
        """Create a new user session"""
        session = UserSession(
            user_id=user_id,
            connection_id=connection_id
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def end_session(
        db: AsyncSession,
        connection_id: str
    ):
        """End a user session"""
        await db.execute(
            update(UserSession)
            .where(UserSession.connection_id == connection_id)
            .values(
                disconnected_at=datetime.utcnow(),
                is_active=False
            )
        )
        await db.commit()

    @staticmethod
    async def get_active_sessions(db: AsyncSession) -> List[UserSession]:
        """Get all active sessions"""
        result = await db.execute(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(UserSession.is_active == True)
        )
        return result.scalars().all()

    @staticmethod
    async def get_online_users(db: AsyncSession) -> List[User]:
        """Get list of currently online users"""
        result = await db.execute(
            select(User)
            .join(UserSession)
            .where(UserSession.is_active == True)
            .distinct()
        )
        return result.scalars().all()