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
    title: str | None = "New Meal"


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


# User Settings schemas
class UserSettingsUpdate(BaseModel):
    macro_enabled: Optional[bool] = None
    protein_pct: Optional[int] = Field(None, ge=0, le=100)
    carbs_pct: Optional[int] = Field(None, ge=0, le=100)
    fat_pct: Optional[int] = Field(None, ge=0, le=100)

    @field_validator('protein_pct', 'carbs_pct', 'fat_pct')
    @classmethod
    def validate_percentages(cls, v, info):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Percentage must be between 0 and 100')
        return v

    def validate_sum(self):
        """Validate that percentages sum to 100 when all are provided"""
        if self.macro_enabled and self.protein_pct is not None and self.carbs_pct is not None and self.fat_pct is not None:
            total = self.protein_pct + self.carbs_pct + self.fat_pct
            if total != 100:
                raise ValueError(f'Macro percentages must sum to 100, got {total}')


class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    macro_enabled: bool
    protein_pct: Optional[int]
    carbs_pct: Optional[int]
    fat_pct: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
