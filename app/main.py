from pathlib import Path
from typing import List
import csv
import io

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app import crud, schemas
from app.llm import LLMService

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

llm_service = LLMService(settings)


@app.get("/api/config")
def get_config():
    """Return public configuration info for display in UI"""
    return {
        "model": settings.ollama_model,
        "api_base": settings.ollama_api_base,
    }


@app.get("/api/chats", response_model=List[schemas.ChatRead])
def list_chats(db: Session = Depends(get_db)):
    return crud.list_chats(db)


@app.post("/api/chats", response_model=schemas.ChatRead)
def create_chat(payload: schemas.ChatCreate, db: Session = Depends(get_db)):
    chat = crud.create_chat(db, title=payload.title)
    return chat


@app.patch("/api/chats/{chat_id}", response_model=schemas.ChatRead)
def rename_chat(
    chat_id: int, payload: schemas.ChatCreate, db: Session = Depends(get_db)
):
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if not payload.title:
        raise HTTPException(status_code=400, detail="Title is required")
    chat = crud.rename_chat(db, chat, payload.title)
    return chat


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    crud.delete_chat(db, chat)
    return {"status": "ok"}


@app.get(
    "/api/chats/{chat_id}/messages", response_model=List[schemas.MessageRead]
)
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return crud.list_messages(db, chat_id)


@app.post("/api/chats/{chat_id}/messages")
def send_message(
    chat_id: int, payload: schemas.MessageCreate, db: Session = Depends(get_db)
):
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    history = crud.list_messages(db, chat_id)
    user_message = crud.add_message(
        db, chat, role="user", content=payload.content
    )

    # Get ingredient data for context
    ingredients = crud.list_ingredients(db)

    assistant_reply = llm_service.chat(
        [*history, user_message], payload.content, ingredients=ingredients
    )
    assistant_message = crud.add_message(
        db, chat, role="assistant", content=assistant_reply
    )

    return {
        "chat_id": chat.id,
        "user_message": user_message.content,
        "assistant_message": assistant_message.content,
    }


@app.post("/api/ingredients/upload")
async def upload_ingredients(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
        
        # Clear existing and save new
        crud.clear_ingredients(db)
        crud.bulk_create_ingredients(db, ingredients_data)
        
        return {"message": f"Successfully uploaded {len(ingredients_data)} ingredients", "count": len(ingredients_data)}
    
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please use UTF-8 encoded CSV")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/api/ingredients/download")
def download_ingredients(db: Session = Depends(get_db)):
    """Download ingredient data as CSV"""
    ingredients = crud.list_ingredients(db)
    
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
def get_ingredients_count(db: Session = Depends(get_db)):
    """Get count of loaded ingredients"""
    ingredients = crud.list_ingredients(db)
    return {"count": len(ingredients)}


# Serve frontend assets
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )
