from pydantic import BaseModel
from typing import Optional

class UserModel(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    user_name: str
    department: str
    bio: Optional[str] = None
    status: Optional[str] = "online"