from fastapi import WebSocket
from typing import Dict
import json
from sqlalchemy.ext.asyncio import AsyncSession
from services.database_service import UserService, MessageService, SessionService
from config.database import AsyncSessionLocal

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_service = UserService()
        self.message_service = MessageService()
        self.session_service = SessionService()

    async def connect(self, websocket: WebSocket, user_id: str, user_name: str = None, department: str = None):
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # Create or update user in database
        async with AsyncSessionLocal() as session:
            await self.user_service.create_or_update_user(
                session, user_id, user_name or user_id, department or "Unknown"
            )

            # Create user session
            connection_id = f"ws_{id(websocket)}"
            await self.session_service.create_session(session, user_id, connection_id)
            await session.commit()

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            connection_id = f"ws_{id(self.active_connections[user_id])}"
            del self.active_connections[user_id]

            # End user session in database
            async with AsyncSessionLocal() as session:
                await self.session_service.end_session(session, user_id, connection_id)
                await session.commit()

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str, exclude_user: str = None, save_to_db: bool = True):
        # Save message to database if requested
        if save_to_db:
            try:
                message_data = json.loads(message)
                if message_data.get("type") == "message" and "text" in message_data:
                    async with AsyncSessionLocal() as session:
                        await self.message_service.create_message(
                            session,
                            text=message_data["text"],
                            message_type=message_data.get("message_type", "text"),
                            user_id=message_data.get("user_id", "system")
                        )
                        await session.commit()
            except (json.JSONDecodeError, KeyError):
                pass

        # Broadcast to all connected users
        for user_id, connection in self.active_connections.items():
            if user_id != exclude_user:
                try:
                    await connection.send_text(message)
                except:
                    pass

    async def get_online_users(self):
        # Get detailed user info from database
        online_user_ids = list(self.active_connections.keys())

        async with AsyncSessionLocal() as session:
            users_data = []
            for user_id in online_user_ids:
                user = await self.user_service.get_user_by_id(session, user_id)
                if user:
                    users_data.append({
                        "user_id": user.user_id,
                        "user_name": user.user_name,
                        "department": user.department
                    })
                else:
                    users_data.append({"user_id": user_id, "user_name": user_id, "department": "Unknown"})

            return {
                "online_users": users_data,
                "count": len(self.active_connections)
            }

    def get_connection_count(self):
        return len(self.active_connections)

    async def get_recent_messages(self, limit: int = 50):
        """Get recent messages from database"""
        async with AsyncSessionLocal() as session:
            messages = await self.message_service.get_recent_messages(session, limit)
            return [message.to_dict() for message in messages]