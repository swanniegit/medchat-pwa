from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import uuid

class User(Base):
    """Database model for users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    user_name = Column(String(200), nullable=False)
    department = Column(String(200), nullable=False)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Relationship to messages
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', user_name='{self.user_name}', department='{self.department}')>"

class Message(Base):
    """Database model for chat messages"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(36), unique=True, index=True, nullable=False)
    text = Column(Text, nullable=False)
    message_type = Column(String(50), default="message", nullable=False)

    # Foreign key to user
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to user
    user = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(message_id='{self.message_id}', user_id='{self.user_id}', type='{self.message_type}')>"

    def to_dict(self):
        """Convert message to dictionary for WebSocket transmission"""
        return {
            "message_id": self.message_id,
            "text": self.text,
            "type": self.message_type,
            "user_id": self.user_id,
            "user_name": self.user.user_name if self.user else None,
            "department": self.user.department if self.user else None,
            "bio": self.user.bio if self.user else None,
            "timestamp": self.created_at.isoformat()
        }

class UserSession(Base):
    """Database model for tracking active user sessions"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False)
    connection_id = Column(String(100), nullable=False)  # WebSocket connection identifier
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship to user
    user = relationship("User")

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', connection_id='{self.connection_id}', active={self.is_active})>"