from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class MessageModel(BaseModel):
    text: str
    user_id: str
    user_name: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    timestamp: Optional[str] = None
    message_id: Optional[str] = None
    type: Optional[str] = "message"

    @classmethod
    def create_system_message(cls, message_type: str, user_id: str, message_text: str):
        return {
            "type": message_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": message_text
        }

    def add_server_metadata(self):
        self.timestamp = datetime.now().isoformat()
        self.message_id = str(uuid.uuid4())
        return self