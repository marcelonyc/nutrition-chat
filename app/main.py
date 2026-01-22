from pathlib import Path
from typing import List
import csv
import io
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app import crud, schemas, models
from app.llm import LLMService
from app.auth import (
    get_current_active_user,
    create_access_token,
    verify_password,
    validate_password_strength
)

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables and ensure data folder exists for SQLite
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.split("sqlite:///")[-1]
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)

# Create admin user if configured
def create_admin_user():
    """Create admin user on startup if configured in .env"""
    if settings.admin_email and settings.admin_user and settings.admin_password:
        db = next(get_db())
        try:
            existing = crud.get_user_by_email(db, settings.admin_email)
            if not existing:
                crud.create_user(
                    db,
                    email=settings.admin_email,
                    username=settings.admin_user,
                    password=settings.admin_password,
                    full_name="Administrator"
                )
                print(f"✓ Admin user created: {settings.admin_user}")
            else:
                print(f"✓ Admin user exists: {settings.admin_user}")
        finally:
            db.close()

create_admin_user()

llm_service = LLMService(settings)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    if crud.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if crud.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create user
    user = crud.create_user(
        db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    return user


@app.post("/api/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and receive JWT access token."""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=schemas.UserProfile)
def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current authenticated user information."""
    return current_user


@app.put("/api/auth/profile", response_model=schemas.UserProfile)
def update_profile(
    profile_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile information."""
    # Check email uniqueness if changing
    if profile_data.email and profile_data.email != current_user.email:
        existing = crud.get_user_by_email(db, profile_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Check username uniqueness if changing
    if profile_data.username and profile_data.username != current_user.username:
        existing = crud.get_user_by_username(db, profile_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    user = crud.update_user(
        db,
        current_user,
        email=profile_data.email,
        username=profile_data.username,
        full_name=profile_data.full_name
    )
    
    return user


@app.post("/api/auth/change-password")
def change_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    crud.change_password(db, current_user, password_data.new_password)
    
    return {"message": "Password changed successfully"}


@app.post("/api/auth/request-password-reset")
def request_password_reset(
    request_data: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset token (in production, send via email)."""
    user = crud.get_user_by_email(db, request_data.email)
    
    # Always return success to prevent email enumeration
    if user:
        token = crud.create_password_reset_token(db, user)
        # In production, send this token via email
        # For now, return it (NOT SECURE FOR PRODUCTION)
        return {
            "message": "Password reset instructions sent to email",
            "token": token  # Remove this in production
        }
    
    return {"message": "Password reset instructions sent to email"}


@app.post("/api/auth/reset-password")
def reset_password(
    reset_data: schemas.PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset password using a valid token."""
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    user = crud.reset_password_with_token(db, reset_data.token, reset_data.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successfully"}


# ============================================================================
# Configuration Endpoints
# ============================================================================

@app.get("/api/config")
def get_config():
    """Return public configuration info for display in UI"""
    return {
        "model": settings.ollama_model,
        "api_base": settings.ollama_api_base,
    }


# ============================================================================
# Chat Endpoints (Protected)
# ============================================================================

@app.get("/api/chats", response_model=List[schemas.ChatRead])
def list_chats(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.list_chats(db, user_id=current_user.id)


@app.post("/api/chats", response_model=schemas.ChatRead)
def create_chat(
    payload: schemas.ChatCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = crud.create_chat(db, user_id=current_user.id, title=payload.title)
    return chat


@app.patch("/api/chats/{chat_id}", response_model=schemas.ChatRead)
def rename_chat(
    chat_id: int,
    payload: schemas.ChatCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = crud.get_chat(db, chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if not payload.title:
        raise HTTPException(status_code=400, detail="Title is required")
    chat = crud.rename_chat(db, chat, payload.title)
    return chat


@app.delete("/api/chats/{chat_id}")
def delete_chat(
    chat_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = crud.get_chat(db, chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    crud.delete_chat(db, chat)
    return {"status": "ok"}


@app.get(
    "/api/chats/{chat_id}/messages", response_model=List[schemas.MessageRead]
)
def get_messages(
    chat_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = crud.get_chat(db, chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return crud.list_messages(db, chat_id)


@app.post("/api/chats/{chat_id}/messages")
def send_message(
    chat_id: int,
    payload: schemas.MessageCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = crud.get_chat(db, chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get user settings to check for macro composition
    settings = crud.get_user_settings(db, user_id=current_user.id)
    
    user_content = payload.content

    history = crud.list_messages(db, chat_id)
    user_message = crud.add_message(
        db, chat, role="user", content=user_content
    )

    # Get ingredient data for context (user-specific)
    ingredients = crud.list_ingredients(db, user_id=current_user.id)

    assistant_reply = llm_service.chat(
        [*history, user_message], user_content, ingredients=ingredients, user_settings=settings
    )
    assistant_message = crud.add_message(
        db, chat, role="assistant", content=assistant_reply
    )

    return {
        "chat_id": chat.id,
        "user_message": user_message.content,
        "assistant_message": assistant_message.content,
    }


# ============================================================================
# Ingredient Endpoints (Protected)
# ============================================================================

@app.post("/api/ingredients/upload")
async def upload_ingredients(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload CSV file with ingredient data. Overwrites existing data."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        
        # Validate columns
        required_cols = {'name', 'calories_per_gram', 'protein_per_gram', 'fat_per_gram', 'carbs_per_gram'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {', '.join(required_cols)}")
        
        # Parse data
        ingredients_data = []
        for row in reader:
            try:
                ingredients_data.append({
                    'name': row['name'].strip(),
                    'calories_per_gram': float(row['calories_per_gram']),
                    'protein_per_gram': float(row['protein_per_gram']),
                    'fat_per_gram': float(row['fat_per_gram']),
                    'carbs_per_gram': float(row['carbs_per_gram'])
                })
            except (ValueError, KeyError) as e:
                raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")
        
        # Clear existing and save new (user-specific)
        crud.clear_ingredients(db, user_id=current_user.id)
        crud.bulk_create_ingredients(db, user_id=current_user.id, ingredients_data=ingredients_data)
        
        return {"message": f"Successfully uploaded {len(ingredients_data)} ingredients", "count": len(ingredients_data)}
    
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please use UTF-8 encoded CSV")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/api/ingredients/download")
def download_ingredients(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download ingredient data as CSV"""
    ingredients = crud.list_ingredients(db, user_id=current_user.id)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'calories_per_gram', 'protein_per_gram', 'fat_per_gram', 'carbs_per_gram'])
    
    for ing in ingredients:
        writer.writerow([ing.name, ing.calories_per_gram, ing.protein_per_gram, ing.fat_per_gram, ing.carbs_per_gram])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ingredients.csv"}
    )


@app.get("/api/ingredients/count")
def get_ingredients_count(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get count of loaded ingredients"""
    ingredients = crud.list_ingredients(db, user_id=current_user.id)
    return {"count": len(ingredients)}


@app.get("/api/ingredients", response_model=list[schemas.IngredientRead])
def list_ingredients(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of all ingredients for current user"""
    ingredients = crud.list_ingredients(db, user_id=current_user.id)
    return ingredients


# ============================================================================
# User Settings Endpoints (Protected)
# ============================================================================

@app.get("/api/settings", response_model=schemas.UserSettingsResponse)
def get_settings(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user settings."""
    settings = crud.get_user_settings(db, user_id=current_user.id)
    return settings


@app.put("/api/settings", response_model=schemas.UserSettingsResponse)
def update_settings(
    settings_data: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user settings."""
    # Validate sum if macro enabled and all percentages provided
    if settings_data.macro_enabled:
        if settings_data.protein_pct is None or settings_data.carbs_pct is None or settings_data.fat_pct is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All macro percentages (protein, carbs, fat) are required when macro composition is enabled"
            )
        
        try:
            settings_data.validate_sum()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    settings = crud.update_user_settings(
        db,
        user_id=current_user.id,
        macro_enabled=settings_data.macro_enabled,
        protein_pct=settings_data.protein_pct,
        carbs_pct=settings_data.carbs_pct,
        fat_pct=settings_data.fat_pct
    )
    return settings


# ============================================================================
# Static Frontend
# ============================================================================

# Serve frontend assets
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )
