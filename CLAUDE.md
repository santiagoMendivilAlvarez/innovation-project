# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BookieWookie is a Django-based full-stack book search and comparison platform targeted at university students in Ciudad Juárez. The application integrates with Google Books and Amazon APIs to search for books, compare prices across platforms, and provides personalized book recommendations using machine learning.

## Development Environment Setup

### Backend Setup (Django)

The backend uses a Python virtual environment located in `backend/venv/`.

**Activate virtual environment:**
```bash
cd backend
.\venv\Scripts\activate  # Windows
```

**Install dependencies:**
```bash
.\venv\Scripts\python.exe -m pip install -r ../requirements.txt
```

**Run development server:**
```bash
.\venv\Scripts\python.exe manage.py runserver
```

**Database migrations:**
```bash
# Create migrations
.\venv\Scripts\python.exe manage.py makemigrations

# Apply migrations (including specific app)
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py migrate chatbot
```

**Access Django admin:**
```
http://127.0.0.1:8000/admin/
```

### Environment Variables

Create a `.env` file in the `backend/` directory with:
- `SECRET_KEY` - Django secret key
- `GOOGLE_BOOKS` - Google Books API key
- `OPENAI_API_KEY` - OpenAI API key for chatbot
- `EMAIL_HOST_USER` - SMTP email for notifications
- `EMAIL_HOST_PASSWORD` - SMTP password
- `AMAZON_ACCESS_KEY_ID` - Amazon API credentials (optional)
- `AMAZON_SECRET_ACCESS_KEY` - Amazon API credentials (optional)
- `RAPIDAPI_KEY` - RapidAPI key for Amazon scraper (optional)

## Architecture

### Django Apps Structure

The backend is organized into 5 main Django apps:

1. **authentication** - Custom user authentication system
   - Custom user model (`CustomUser`) extending Django's `AbstractUser`
   - Fields: nombre_completo, universidad, carrera, nivel_academico, email_verificado, suscripcion_activa, intereses_usuario
   - Email-based authentication (email as USERNAME_FIELD)
   - Email verification system (can be toggled via `SKIP_EMAIL_VERIFICATION` setting)

2. **libros** - Book catalog and search functionality
   - Models: `Libro`, `Categoria`, `FuenteLibro` (book sources/platforms), `Resena` (reviews)
   - Views handle book search, detail views, and explore functionality
   - Integrates with Google Books and Amazon APIs via `core.api` modules

3. **chatbot** - AI-powered book recommendation chatbot
   - Uses OpenAI GPT-4o-mini for conversational interface
   - Models: `ConversacionChat`, `MensajeChat`
   - Stores conversation history in database
   - Cache-backed for performance
   - System prompt includes special `[SEARCH:term]` syntax for book searches

4. **profiles** - User profiles and preferences
   - Models: `Favorito`, `Recomendacion`, `InteresUsuario`
   - Tracks user book favorites, recommendations from others, and category interests
   - `InteresUsuario` links users to categories with interest levels (1-10)

5. **core** - Shared services and utilities
   - `core/api/` - External API integrations (Google Books, Amazon)
   - `core/services/recommendation_service.py` - Machine learning recommendation engine
   - `core/sessions/` - Session management utilities

### Machine Learning Recommendation System

Located in `backend/core/services/recommendation_service.py`:

**Class:** `RecomendationEngine`

**Key Features:**
- Collaborative filtering using cosine similarity
- Combines user interests (70%) and collaborative recommendations (30%)
- Uses sklearn for feature engineering and similarity calculations
- Persists trained model to `backend/ml_models/recommendation_model.pkl`
- Cache-backed recommendations (1-hour TTL)
- Cold-start handling for new users based on interests or popular books

**Main Methods:**
- `prepare_user_features()` - Builds user-category feature matrix from interests and favorites
- `prepare_collaborative_features()` - Builds collaborative filtering features from recommendations
- `train()` - Trains similarity matrix and saves model
- `get_recommendations(user_id, top_n)` - Returns personalized book recommendations
- `get_similar_books(libro_id, top_n)` - Returns books similar to a given book
- `_cold_start_recommendations()` - Fallback for users without history

**Data Flow:**
1. User favorites → boost score by 5x
2. User category interests → weighted by nivel_interes (1-10)
3. Recommendation ratings → averaged per category
4. Features normalized with MinMaxScaler
5. Cosine similarity computed between users
6. Similar users' favorites recommended (excluding user's own favorites)
7. Results boosted by user's category interests

### External API Integration

**Google Books API** (`core/api/google_books.py`):
- Smart search: tries ISBN first, then general search, then related subjects
- Cache-backed with Django's cache framework
- Fallback when API key not configured

**Amazon API** (`core/api/amazon_books.py`):
- Supports both official Amazon Product Advertising API and RapidAPI scraper
- Price comparison functionality

### Template Structure

- `backend/templates/utils/` - Base templates and navigation
  - `base.html` - Main template
  - `nav_auth.html` - Authenticated user navigation
  - `nav_guest.html` - Guest navigation
- App-specific templates in `backend/{app_name}/templates/`

## Database

- **Default:** SQLite3 (`backend/db.sqlite3`)
- **Custom User Model:** `authentication.CustomUser` (set via `AUTH_USER_MODEL`)
- **Caching:** Local memory cache (`LocMemCache`)

## Common Tasks

### Training the Recommendation Model

```python
from core.services.recommendation_service import RecomendationEngine

engine = RecomendationEngine()
engine.train()  # Saves to ml_models/recommendation_model.pkl
```

### Getting Recommendations

```python
from core.services.recommendation_service import RecomendationEngine

engine = RecomendationEngine()
recommendations = engine.get_recommendations(user_id=1, top_n=10)
```

### Searching Books

The book search view (`libros.views.book_search_view`) integrates multiple sources:
- Google Books API
- Amazon API (if configured)
- Local database books

### Creating Default Categories

Default categories are auto-created via post-migration signal in `libros/models.py`:
- Ciencia y Tecnología
- Literatura
- Historia
- Psicología
- Filosofía
- Matemáticas
- Arte y Diseño
- Negocios

## URL Structure

- `/` - Home page
- `/auth/` - Authentication routes (login, register, password reset)
- `/chatbot/` - AI chatbot interface
- `/perfil/` - User profile and library
- `/admin/` - Django admin interface

## Settings Notes

- **Language:** Spanish (`es-es`)
- **Timezone:** America/Mexico_City
- **Debug Mode:** Currently enabled (disable in production)
- **Email Verification:** Can be skipped via `SKIP_EMAIL_VERIFICATION = True`
- **CSRF:** Configured for localhost development
- **Static Files:** Located in `backend/static/` and `backend/staticfiles/`
- **Media Files:** User uploads in `backend/media/`

## Git Workflow

- **Main branch:** `main`
- **Current feature branch:** `feature/searcher`
- Use pull requests to merge features into main

## Key Dependencies

- Django 5.2.4
- OpenAI 2.6.0 (chatbot)
- scikit-learn 1.7.2 (recommendations)
- pandas 2.3.3 (data processing)
- requests 2.32.4 (API calls)
- BeautifulSoup4 4.12.3 (web scraping)

## Important Considerations

### When Working with User Model
- Always use `get_user_model()` to reference the user model
- User interests are stored as JSON string in `intereses_usuario` field
- Use `set_intereses()` and `get_intereses_list()` methods to manage interests

### When Working with Recommendations
- Recommendation model must be trained before getting personalized recommendations
- Model automatically handles cold-start scenarios
- Cache is used extensively - clear cache if recommendations seem stale

### When Working with Book Search
- Google Books API has rate limits - implement appropriate caching
- Search supports multiple fallback strategies
- Amazon integration is optional and requires proper credentials

### When Working with Chatbot
- Chatbot uses conversation history (last 20 messages)
- Special `[SEARCH:term]` syntax in responses creates clickable search links
- Conversations have states: activa, inactiva, cerrada
