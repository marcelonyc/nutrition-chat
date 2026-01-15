from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app import models


def list_chats(db: Session):
    stmt = select(models.ChatSession).order_by(
        desc(models.ChatSession.updated_at)
    )
    return db.scalars(stmt).all()


def get_chat(db: Session, chat_id: int) -> models.ChatSession | None:
    return db.get(models.ChatSession, chat_id)


def create_chat(db: Session, title: str | None = None) -> models.ChatSession:
    chat = models.ChatSession(title=title or "New Chat")
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def rename_chat(
    db: Session, chat: models.ChatSession, title: str
) -> models.ChatSession:
    chat.title = title
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def delete_chat(db: Session, chat: models.ChatSession):
    db.delete(chat)
    db.commit()


def list_messages(db: Session, chat_id: int):
    stmt = (
        select(models.Message)
        .where(models.Message.chat_id == chat_id)
        .order_by(models.Message.created_at)
    )
    return db.scalars(stmt).all()


def add_message(
    db: Session, chat: models.ChatSession, role: str, content: str
) -> models.Message:
    from datetime import datetime
    
    message = models.Message(chat_id=chat.id, role=role, content=content)
    db.add(message)
    chat.updated_at = datetime.utcnow()
    db.add(chat)
    db.commit()
    db.refresh(message)
    db.refresh(chat)
    return message


def list_ingredients(db: Session):
    stmt = select(models.Ingredient).order_by(models.Ingredient.name)
    return db.scalars(stmt).all()


def clear_ingredients(db: Session):
    db.query(models.Ingredient).delete()
    db.commit()


def bulk_create_ingredients(db: Session, ingredients_data: list[dict]):
    ingredients = [models.Ingredient(**data) for data in ingredients_data]
    db.bulk_save_objects(ingredients)
    db.commit()
