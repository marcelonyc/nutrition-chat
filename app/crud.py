from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime, timedelta
import secrets
from typing import Optional

from app import models
from app.auth import get_password_hash, verify_password


# User operations
def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email."""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username."""
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None
) -> models.User:
    """Create a new user."""
    hashed_password = get_password_hash(password)
    user = models.User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticate a user by username/email and password."""
    # Try username first
    user = get_user_by_username(db, username)
    if not user:
        # Try email
        user = get_user_by_email(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def update_user(
    db: Session,
    user: models.User,
    email: Optional[str] = None,
    username: Optional[str] = None,
    full_name: Optional[str] = None
) -> models.User:
    """Update user profile."""
    if email is not None:
        user.email = email
    if username is not None:
        user.username = username
    if full_name is not None:
        user.full_name = full_name
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: models.User, new_password: str) -> models.User:
    """Change user password."""
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_password_reset_token(db: Session, user: models.User) -> str:
    """Create a password reset token for the user."""
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.add(user)
    db.commit()
    return token


def verify_reset_token(db: Session, token: str) -> Optional[models.User]:
    """Verify password reset token and return user if valid."""
    user = db.query(models.User).filter(
        models.User.reset_token == token,
        models.User.reset_token_expires > datetime.utcnow()
    ).first()
    return user


def reset_password_with_token(db: Session, token: str, new_password: str) -> Optional[models.User]:
    """Reset password using a valid token."""
    user = verify_reset_token(db, token)
    if not user:
        return None
    
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Chat operations
def list_chats(db: Session, user_id: int):
    stmt = select(models.ChatSession).where(
        models.ChatSession.user_id == user_id
    ).order_by(desc(models.ChatSession.updated_at))
    return db.scalars(stmt).all()


def get_chat(db: Session, chat_id: int, user_id: int) -> models.ChatSession | None:
    return db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_id,
        models.ChatSession.user_id == user_id
    ).first()


def create_chat(db: Session, user_id: int, title: str | None = None) -> models.ChatSession:
    chat = models.ChatSession(user_id=user_id, title=title or "New Chat")
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


# Message operations
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
    message = models.Message(chat_id=chat.id, role=role, content=content)
    db.add(message)
    chat.updated_at = datetime.utcnow()
    db.add(chat)
    db.commit()
    db.refresh(message)
    db.refresh(chat)
    return message


# Ingredient operations
def list_ingredients(db: Session, user_id: int):
    stmt = select(models.Ingredient).where(
        models.Ingredient.user_id == user_id
    ).order_by(models.Ingredient.name)
    return db.scalars(stmt).all()


def clear_ingredients(db: Session, user_id: int):
    db.query(models.Ingredient).filter(models.Ingredient.user_id == user_id).delete()
    db.commit()


def bulk_create_ingredients(db: Session, user_id: int, ingredients_data: list[dict]):
    ingredients = [
        models.Ingredient(user_id=user_id, **data)
        for data in ingredients_data
    ]
    db.bulk_save_objects(ingredients)
    db.commit()
