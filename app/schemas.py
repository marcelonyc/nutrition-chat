from datetime import datetime
from pydantic import BaseModel
from typing import List


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
    title: str | None = None


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
