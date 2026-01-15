from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# Message schemas
class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    title: str | None = "New Chat"


class ChatRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatDetail(ChatRead):
    messages: List[MessageRead] = []


class IngredientBase(BaseModel):
    name: str
    calories_per_gram: float
    protein_per_gram: float
    fat_per_gram: float
    carbs_per_gram: float


class IngredientRead(IngredientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
