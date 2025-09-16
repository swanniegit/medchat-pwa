from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import List, Dict, Optional
import json
import uuid
import re
import hashlib
import secrets
from datetime import datetime, timedelta
import html

# Optional security imports (install with: pip install -r requirements.txt)
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    print("⚠️  Warning: bleach not installed. HTML sanitization disabled.")
    print("🔧 Run: pip install bleach for full security features")

app = FastAPI(title="Nightingale-Chat API", version="1.0.0")

# Security middleware for headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000", "http://localhost:3000"],  # More restrictive
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["*"],
)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}

# Security utilities
class SecurityUtils:
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not text:
            return ""

        # Limit length
        text = text[:max_length]

        # Remove HTML tags and escape special characters
        if BLEACH_AVAILABLE:
            text = bleach.clean(text, tags=[], strip=True)

        text = html.escape(text)

        return text.strip()

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        if not user_id or len(user_id) > 100:
            return False

        # Only allow alphanumeric, underscore, and hyphen
        return re.match(r'^[a-zA-Z0-9_-]+$', user_id) is not None

    @staticmethod
    def validate_message_length(message: str) -> bool:
        """Validate message length"""
        return 0 < len(message) <= 1000

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt + pwd_hash.hex()

    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        """Verify password against hash"""
        salt = stored_password[:64]
        stored_hash = stored_password[64:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwd_hash.hex() == stored_hash

    @staticmethod
    def check_rate_limit(client_id: str, max_requests: int = 30, time_window: int = 60) -> bool:
        """Simple rate limiting"""
        now = datetime.now()

        if client_id not in rate_limit_storage:
            rate_limit_storage[client_id] = []

        # Clean old entries
        rate_limit_storage[client_id] = [
            timestamp for timestamp in rate_limit_storage[client_id]
            if (now - timestamp).seconds < time_window
        ]

        # Check if limit exceeded
        if len(rate_limit_storage[client_id]) >= max_requests:
            return False

        # Add current request
        rate_limit_storage[client_id].append(now)
        return True

security = SecurityUtils()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.users: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.users:
            del self.users[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str, exclude_user: str = None):
        for user_id, connection in self.active_connections.items():
            if user_id != exclude_user:
                try:
                    await connection.send_text(message)
                except:
                    pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Nightingale-Chat API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_users": len(manager.active_connections)}

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

    await manager.connect(websocket, user_id)

    # Send user joined notification
    join_message = {
        "type": "user_joined",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "message": f"User {user_id} joined the chat"
    }
    await manager.broadcast(json.dumps(join_message), exclude_user=user_id)

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

            # Sanitize other text fields
            for field in ["user_name", "department", "bio"]:
                if field in message_data:
                    message_data[field] = security.sanitize_input(message_data[field], 200)

            # Add server-side metadata
            message_data.update({
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4())
            })

            # Broadcast message to all connected users
            await manager.broadcast(json.dumps(message_data), exclude_user=user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)

        # Send user left notification
        leave_message = {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"User {user_id} left the chat"
        }
        await manager.broadcast(json.dumps(leave_message))

@app.get("/users/online")
async def get_online_users():
    return {
        "online_users": list(manager.active_connections.keys()),
        "count": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    import os

    # For local development with HTTPS (create self-signed certs)
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
        print("⚠️  Starting with HTTP (create SSL certs for HTTPS)")
        uvicorn.run(app, host="0.0.0.0", port=8000)