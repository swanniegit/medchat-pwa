from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json
import uuid
from contextlib import asynccontextmanager

# Import modular components
from security.middleware import SecurityHeadersMiddleware
from security.utils import SecurityUtils
from services.websocket_manager import ConnectionManager
from services.database_service import MessageService, UserService
from config.database import init_db, close_db, AsyncSessionLocal
from models.db_models import Message

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    yield
    # Close database connections on shutdown
    await close_db()

app = FastAPI(title="Nightingale-Chat API", version="1.0.0", lifespan=lifespan)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize components
security = SecurityUtils()
manager = ConnectionManager()
message_service = MessageService()
user_service = UserService()

@app.get("/")
async def root():
    return {"message": "Nightingale-Chat API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_users": manager.get_connection_count()}

@app.get("/users/online")
async def get_online_users():
    return await manager.get_online_users()

@app.get("/messages/recent")
async def get_recent_messages(limit: int = 50):
    """Get recent messages from database"""
    return await manager.get_recent_messages(limit)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # Validate user ID format
    if not security.validate_user_id(user_id):
        await websocket.close(code=4000, reason="Invalid user ID format")
        return

    # Rate limiting check
    client_host = websocket.client.host if websocket.client else "unknown"
    if not security.check_rate_limit(f"ws_{client_host}_{user_id}", max_requests=5, time_window=60):
        await websocket.close(code=4029, reason="Rate limit exceeded")
        return

    # Extract user info from first message or use defaults
    user_name = user_id  # Default to user_id
    department = "Unknown"  # Default department

    await manager.connect(websocket, user_id, user_name, department)

    # Send user joined notification
    join_message = {
        "type": "user_joined",
        "user_id": user_id,
        "text": f"User {user_id} joined the chat",
        "timestamp": datetime.now().isoformat(),
        "message_id": str(uuid.uuid4())
    }
    await manager.broadcast(json.dumps(join_message), exclude_user=user_id, save_to_db=False)

    try:
        while True:
            data = await websocket.receive_text()

            # Rate limit messages
            if not security.check_rate_limit(f"msg_{user_id}", max_requests=20, time_window=60):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Rate limit exceeded. Please slow down."
                }))
                continue

            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                }))
                continue

            # Validate and sanitize message content
            if "text" in message_data:
                text = message_data["text"]

                if not security.validate_message_length(text):
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Message too long or empty"
                    }))
                    continue

                # Sanitize message text
                message_data["text"] = security.sanitize_input(text, 1000)

            # Update user info if provided
            if "user_name" in message_data or "department" in message_data:
                async with AsyncSessionLocal() as session:
                    user_name = security.sanitize_input(message_data.get("user_name", ""), 200) if "user_name" in message_data else None
                    department = security.sanitize_input(message_data.get("department", ""), 200) if "department" in message_data else None

                    if user_name or department:
                        await user_service.update_user_info(session, user_id, user_name, department)
                        await session.commit()

            # Add server-side metadata
            message_data.update({
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4()),
                "user_id": user_id
            })

            # Broadcast message to all connected users (will be saved to DB in broadcast method)
            await manager.broadcast(json.dumps(message_data), exclude_user=user_id)

    except WebSocketDisconnect:
        await manager.disconnect(user_id)

        # Send user left notification
        leave_message = {
            "type": "user_left",
            "user_id": user_id,
            "text": f"User {user_id} left the chat",
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        await manager.broadcast(json.dumps(leave_message), save_to_db=False)

# Mount static files - adjust path for Docker working directory
app.mount("/frontend", StaticFiles(directory="../frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import os

    # For local development with HTTPS
    ssl_keyfile = "key.pem"
    ssl_certfile = "cert.pem"

    # Check if SSL certificates exist
    if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        print("🔒 Starting with HTTPS/TLS")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        print("⚠️  Starting without HTTPS")
        uvicorn.run(app, host="0.0.0.0", port=8000)