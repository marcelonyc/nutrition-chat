# Nutrition Chat

A full-stack LLM chat application with user authentication, built with FastAPI, SQLite, and Ollama. Manage personal chat sessions, upload nutritional data, and get AI-powered dietary advice with complete user segregation and security.

## Features
- 🔐 **User Authentication** - Secure registration, login, and JWT-based authentication
- 👤 **User Profiles** - Manage your profile, change password, and password reset
- 💬 **Personal Chat Sessions** - Each user has their own isolated chat history
- 📊 **Private Ingredient Database** - Upload and manage your own nutritional data (CSV)
- 🤖 **Ollama LLM Integration** - Customizable system prompts and model selection
- 📝 **Markdown Support** - Rich formatted responses with code highlighting
- 🎨 **Modern Dark UI** - Responsive design that works on desktop and mobile
- 🔒 **Data Segregation** - Your chats and data are private and isolated from other users

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) running locally with your chosen model (e.g., `ollama pull llama3.2:1b`)

## Quick Start

### 1. Clone and Setup
```bash
# Copy environment configuration
cp .env.example .env

# Edit .env and set your configuration (especially SECRET_KEY for production!)
# Set ADMIN_EMAIL, ADMIN_USER, and ADMIN_PASSWORD to create a default admin account
```

### 2. Install Dependencies
```bash
# Consider using a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0
```

### 4. Access the Application
- **Web UI**: http://localhost:8000
- **Login Page**: http://localhost:8000/login.html
- **API Docs**: http://localhost:8000/docs

## Configuration (.env)

### Application Settings
- `APP_NAME`: Application name (default: "Nutrition Chat")

### LLM Configuration
- `OLLAMA_MODEL`: Model name (e.g., `llama3.2:1b`)
- `OLLAMA_API_BASE`: Ollama server URL (default: `http://localhost:11434`)
- `OLLAMA_API_TOKEN`: Optional API token for Ollama cloud models
- `SYSTEM_PROMPT`: Custom system prompt for the LLM
- `MEMORY_TOKEN_LIMIT`: Token window for chat context (default: 3200)

### Database Configuration
- `DATABASE_URL`: Connection string (default: `sqlite:///./data/chat.db`)

### Security Settings (IMPORTANT!)
- `SECRET_KEY`: JWT secret key - **MUST BE CHANGED IN PRODUCTION!**
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry time (default: 10080 = 7 days)

### Admin Account (Optional)
- `ADMIN_EMAIL`: Admin user email
- `ADMIN_USER`: Admin username
- `ADMIN_PASSWORD`: Admin password (created on first startup)

## User Guide

### Registration & Login
1. Navigate to http://localhost:8000 (redirects to login if not authenticated)
2. Click "Register" tab to create a new account
3. Password requirements:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number

### Password Management
- **Change Password**: Access from user profile menu
- **Reset Password**: Click "Forgot password?" on login page
  - Note: In development, reset tokens are returned in the API response
  - In production, tokens should be sent via email

### Managing Chats
 - **New Meal**: Click "+ New Meal" button
- **Rename**: Click ✏️ icon on any chat
- **Delete**: Click 🗑️ icon and confirm
- **Switch Chat**: Click on any chat in the list

### Ingredient Database
Each user has their own private ingredient database.

**Upload CSV** (per-user data):
```csv
name,calories_per_gram,protein_per_gram,fat_per_gram,carbs_per_gram
Chicken Breast,1.65,0.31,0.036,0
Brown Rice,1.12,0.026,0.009,0.233
Broccoli,0.34,0.028,0.004,0.07
Salmon,2.08,0.20,0.13,0
Almonds,5.79,0.21,0.50,0.22
```

**Features**:
- Upload overwrites your existing data
- Download your current ingredient database
- LLM automatically references your data when answering nutrition questions
- Ingredient count displayed in sidebar

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Login and receive JWT token
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password
- `POST /api/auth/request-password-reset` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token

### Chats (Protected)
- `GET /api/chats` - List user's chats
- `POST /api/chats` - Create new meal
- `PATCH /api/chats/{id}` - Rename chat
- `DELETE /api/chats/{id}` - Delete chat
- `GET /api/chats/{id}/messages` - Get chat messages
- `POST /api/chats/{id}/messages` - Send message

### Ingredients (Protected)
- `POST /api/ingredients/upload` - Upload CSV
- `GET /api/ingredients/download` - Download CSV
- `GET /api/ingredients/count` - Get ingredient count

### Public
- `GET /api/config` - Get public configuration

## Security Features

### Password Security
- Bcrypt hashing with automatic salt generation
- Password strength validation
- Secure password reset with time-limited tokens

### Authentication
- JWT (JSON Web Tokens) for stateless authentication
- 7-day token expiry (configurable)
- Automatic logout on token expiry
- Protected API endpoints require authentication

### Data Privacy
- User-specific data segregation
- Chats isolated per user
- Ingredients database separated per user
- No cross-user data access

### Best Practices for Production
1. **Generate a secure SECRET_KEY**:
   ```python
   import secrets
   secrets.token_urlsafe(32)
   ```
2. Set up HTTPS/TLS for encrypted communication
3. Configure CORS to allow only trusted origins
4. Set up proper email service for password resets
5. Use environment variables, never commit .env files
6. Consider implementing rate limiting
7. Regular security updates and audits

## Project Structure
```
nutrition-chat/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, endpoints, admin user creation
│   ├── auth.py           # Authentication utilities (JWT, password hashing)
│   ├── config.py         # Configuration management
│   ├── crud.py           # Database operations (user + chat + ingredients)
│   ├── database.py       # SQLAlchemy setup
│   ├── models.py         # Database models (User, ChatSession, Message, Ingredient)
│   ├── schemas.py        # Pydantic schemas for API validation
│   └── llm.py           # LLM service (Ollama integration)
├── frontend/
│   ├── index.html        # Main chat application (authenticated)
│   └── login.html        # Login/register page
├── data/
│   └── chat.db          # SQLite database (auto-created)
├── .env                 # Configuration (create from .env.example)
├── .env.example         # Example configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Mobile Support
The application is fully responsive and works on mobile devices:
- Touch-optimized sidebar navigation
- Hamburger menu for mobile screens
- Responsive layouts and controls
- Touch-friendly buttons and inputs

## Development

### Database Migrations
The application automatically creates database tables on startup. If you modify models:
1. Delete `data/chat.db` (loses all data)
2. Or use Alembic for proper migrations (recommended for production)

### Adding New Features
- Backend: Add endpoints in [app/main.py](app/main.py)
- Database: Add models in [app/models.py](app/models.py)
- Frontend: Update [frontend/index.html](frontend/index.html)

### Testing API
Use the interactive API documentation at http://localhost:8000/docs:
1. Click "Authorize" button
2. Login via `/api/auth/login` endpoint
3. Copy the `access_token` from response
4. Use it in the "Authorize" dialog (format: `Bearer <token>`)

## Troubleshooting

### Can't Login / 401 Errors
- Ensure the server is running
- Check if SECRET_KEY is set in .env
- Verify user account exists (or create via register)

### Database Errors
- Ensure `data/` directory exists and is writable
- Check DATABASE_URL in .env
- Delete `data/chat.db` to reset (loses all data)

### Ollama Connection Issues
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check OLLAMA_API_BASE in .env
- Ensure the model is pulled: `ollama pull llama3.2:1b`

### Token Expired
- Tokens expire after 7 days by default
- Simply log in again to get a new token
- Adjust ACCESS_TOKEN_EXPIRE_MINUTES in .env if needed

## License
MIT

## Contributing
Contributions welcome! Please feel free to submit a Pull Request.
