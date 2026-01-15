# Nutrition Chat

A minimal full-stack LLM chat app built with FastAPI, SQLite, and Ollama. The web UI lets you create, rename, delete, and chat within saved conversations. Upload ingredient nutritional data to enhance the LLM's responses with specific dietary information.

## Features
- 💬 Persistent chat sessions with full history
- 🤖 Ollama LLM integration with custom system prompts
- 📊 CSV ingredient database (calories, protein, fat, carbs per gram)
- 📝 Markdown rendering for formatted responses
- 🎨 Dark theme UI with responsive design

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) running locally with the model you want (e.g. `ollama pull llama3.2:1b`)

## Setup
1. Copy the example env and adjust values:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies (consider a virtualenv):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API and web UI:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0
   ```
4. Open http://localhost:8000 in your browser. The FastAPI docs are at http://localhost:8000/docs.

## Configuration (.env)
- `OLLAMA_MODEL`: Model name served by Ollama (e.g. `llama3.2:1b`)
- `OLLAMA_API_BASE`: Ollama base URL (default: `http://localhost:11434`)
- `OLLAMA_API_TOKEN`: Optional API token for Ollama cloud models
- `SYSTEM_PROMPT`: Custom system prompt for the LLM
- `DATABASE_URL`: Database connection string (default SQLite under `./data/chat.db`)
- `MEMORY_TOKEN_LIMIT`: Token window for in-memory chat context
- `ADMIN_USER` / `ADMIN_PASSWORD`: Reserved for future authentication hooks

## Ingredient Data
Upload a CSV file with nutritional information to enhance the LLM's knowledge:

**CSV Format:**
```csv
name,calories_per_gram,protein_per_gram,fat_per_gram,carbs_per_gram
Chicken Breast,1.65,0.31,0.036,0
Brown Rice,1.12,0.026,0.009,0.233
Broccoli,0.34,0.028,0.004,0.07
```

Use the "Upload CSV" button in the sidebar to load data. The LLM will reference this data when answering nutrition questions.

## Project structure
- `app/` FastAPI app, database models, and LLM service
- `frontend/` Static HTML/JS single-page UI

## Notes
- Chat history persists in the configured database and is replayed into the LLM memory buffer per request.
- Ingredient data is automatically included in the LLM's system context when available.
- Upload overwrites existing ingredient data.
- If you change the database path to a new location, ensure its parent folder exists or update permissions accordingly.
