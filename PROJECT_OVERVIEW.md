# Personal Podcast Generator - Project Overview

## Project Status: INITIALIZED ✓

Complete project structure has been set up for the Prosper AI hiring project.

---

## 📁 Project Structure

```
personal-podcast-generator/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── models/                   # ✓ Database models (User, Podcast, Metrics)
│   │   │   ├── user.py              # ✓ User model with preferences
│   │   │   ├── podcast.py           # ✓ Podcast model with status tracking
│   │   │   └── metrics.py           # ✓ Analytics metrics model
│   │   ├── services/                 # Business logic services
│   │   │   └── __init__.py          # ✓ Ready for implementation
│   │   ├── api/                      # API endpoints
│   │   │   └── __init__.py          # ✓ Ready for implementation
│   │   ├── core/                     # Core configuration
│   │   │   ├── config.py            # ✓ Settings with Pydantic
│   │   │   └── database.py          # ✓ Async SQLAlchemy setup
│   │   └── main.py                   # ✓ FastAPI app with CORS
│   ├── alembic/                      # Database migrations
│   │   ├── versions/                 # Migration files directory
│   │   ├── env.py                    # ✓ Async migration config
│   │   └── script.py.mako           # ✓ Migration template
│   ├── requirements.txt              # ✓ All Python dependencies
│   ├── alembic.ini                  # ✓ Alembic configuration
│   └── .env.example                 # ✓ Environment variables template
│
├── frontend/                         # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/              # Reusable React components
│   │   ├── pages/                   # Page components
│   │   ├── services/                # API client services
│   │   ├── types/                   # TypeScript definitions
│   │   ├── App.tsx                  # ✓ Main app component
│   │   ├── main.tsx                 # ✓ Entry point
│   │   └── index.css                # ✓ Tailwind CSS setup
│   ├── package.json                 # ✓ Node dependencies
│   ├── tsconfig.json                # ✓ TypeScript config
│   ├── vite.config.ts               # ✓ Vite with proxy setup
│   ├── tailwind.config.js           # ✓ Tailwind configuration
│   ├── postcss.config.js            # ✓ PostCSS setup
│   ├── .eslintrc.cjs                # ✓ ESLint configuration
│   └── index.html                   # ✓ HTML template
│
├── docker-compose.yml               # ✓ Docker orchestration
├── .gitignore                       # ✓ Git ignore rules
├── README.md                        # ✓ Project documentation
├── SETUP.md                         # ✓ Detailed setup guide
└── PROJECT_OVERVIEW.md              # ✓ This file

Total Files Created: 30+
```

---

## 🛠 Technology Stack

### Backend (Python)
- **FastAPI 0.115.0** - Modern async web framework
- **SQLAlchemy 2.0.36** - Async ORM with PostgreSQL
- **Alembic 1.14.0** - Database migrations
- **Pydantic 2.9.2** - Data validation
- **asyncpg 0.29.0** - Async PostgreSQL driver
- **OpenAI 1.54.3** - GPT-4 for script generation
- **ElevenLabs 1.10.0** - Text-to-speech synthesis
- **Firecrawl 1.5.1** - Web scraping

### Frontend (TypeScript)
- **React 18.3.1** - UI library
- **TypeScript 5.6.3** - Type safety
- **Vite 5.4.11** - Build tool
- **Tailwind CSS 3.4.15** - Styling
- **React Router 6.28.0** - Routing
- **Recharts 2.13.3** - Charts
- **Lucide React 0.462.0** - Icons
- **Axios 1.7.7** - HTTP client

### Infrastructure
- **PostgreSQL 15** - Database
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

---

## 🗄 Database Schema (Already Defined)

### Users Table
```python
- id: UUID (PK)
- preferences: JSONB (interests, topics, sources)
- schedule_settings: JSONB (frequency, time, timezone)
- created_at: DateTime
- updated_at: DateTime
```

### Podcasts Table
```python
- id: UUID (PK)
- user_id: UUID (FK -> users.id)
- script: Text (generated script)
- audio_url: String (S3 or local path)
- status: Enum (PENDING, PROCESSING, COMPLETED, FAILED)
- error_message: Text (optional)
- metadata: Text (JSON format)
- created_at: DateTime
- updated_at: DateTime
```

### Metrics Table
```python
- id: UUID (PK)
- podcast_id: UUID (FK -> podcasts.id)
- script_generation_time: Float (seconds)
- audio_generation_time: Float (seconds)
- total_words: Integer
- audio_duration: Float (seconds)
- topics_covered: JSONB
- created_at: DateTime
```

---

## 🚀 Quick Start Commands

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up -d
```

---

## 📋 Next Implementation Steps

### Phase 1: Core Services (Recommended Order)
1. **Firecrawl Service** (`backend/app/services/scraper.py`)
   - Implement web scraping
   - Extract and clean content
   - Handle multiple URLs

2. **OpenAI Service** (`backend/app/services/script_generator.py`)
   - Generate podcast scripts from content
   - Format dialogue with multiple speakers
   - Add transitions and intros/outros

3. **ElevenLabs Service** (`backend/app/services/audio_generator.py`)
   - Text-to-speech conversion
   - Multi-voice support
   - Audio file management

### Phase 2: API Endpoints
4. **User Endpoints** (`backend/app/api/users.py`)
   - Create user
   - Update preferences
   - Get user settings

5. **Podcast Endpoints** (`backend/app/api/podcasts.py`)
   - Generate podcast (POST)
   - Get podcast status (GET)
   - List user podcasts (GET)
   - Stream/download audio (GET)

6. **Metrics Endpoints** (`backend/app/api/metrics.py`)
   - Get podcast metrics
   - Get user statistics
   - Dashboard analytics

### Phase 3: Frontend Pages
7. **Landing Page** (`frontend/src/pages/Landing.tsx`)
   - Hero section
   - Feature showcase
   - Call-to-action

8. **Generation Page** (`frontend/src/pages/Generate.tsx`)
   - URL input form
   - Real-time progress
   - Error handling

9. **Library Page** (`frontend/src/pages/Library.tsx`)
   - List all podcasts
   - Filter/search
   - Play/download

10. **Dashboard Page** (`frontend/src/pages/Dashboard.tsx`)
    - Analytics charts (Recharts)
    - Usage statistics
    - Generation metrics

### Phase 4: Advanced Features
11. **Background Task Queue**
    - Celery or FastAPI BackgroundTasks
    - Async podcast generation
    - Status updates via WebSocket

12. **File Storage**
    - AWS S3 integration
    - Local file storage (dev)
    - Presigned URLs

13. **Testing**
    - Backend: pytest
    - Frontend: Vitest
    - Integration tests

---

## 🔑 Required API Keys

Get these API keys before starting development:

1. **OpenAI** - https://platform.openai.com/api-keys
   - Used for: Script generation (GPT-4)
   - Cost: ~$0.01-0.03 per podcast

2. **ElevenLabs** - https://elevenlabs.io/
   - Used for: Text-to-speech
   - Free tier: 10,000 characters/month
   - Cost: $5/month for 30,000 characters

3. **Firecrawl** - https://www.firecrawl.dev/
   - Used for: Web scraping
   - Free tier: 500 pages/month
   - Cost: $20/month for 5,000 pages

---

## 📝 Environment Setup

### Backend `.env` file
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/podcast_generator
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...
ENVIRONMENT=development
DEBUG=True
```

### Database Setup (PostgreSQL)
```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt install postgresql  # Ubuntu

# Start PostgreSQL
brew services start postgresql  # macOS
sudo service postgresql start  # Ubuntu

# Create database
createdb podcast_generator
```

---

## 🎯 Key Features to Implement

### Core Features
- ✅ Project structure
- ✅ Database models
- ✅ Configuration management
- ⏳ Web content scraping
- ⏳ AI script generation
- ⏳ Multi-voice audio synthesis
- ⏳ Podcast library management
- ⏳ Analytics dashboard

### Advanced Features (Future)
- ⏳ User authentication (JWT)
- ⏳ Scheduled podcast generation
- ⏳ RSS feed integration
- ⏳ Email notifications
- ⏳ Social sharing
- ⏳ Custom voice selection
- ⏳ Podcast templates
- ⏳ Export to multiple formats

---

## 📊 API Endpoints (To Implement)

```
POST   /api/v1/users                 # Create user
GET    /api/v1/users/{id}            # Get user
PUT    /api/v1/users/{id}            # Update user preferences

POST   /api/v1/podcasts              # Generate podcast
GET    /api/v1/podcasts              # List podcasts
GET    /api/v1/podcasts/{id}         # Get podcast details
GET    /api/v1/podcasts/{id}/audio   # Stream audio
DELETE /api/v1/podcasts/{id}         # Delete podcast

GET    /api/v1/metrics               # Get user metrics
GET    /api/v1/metrics/dashboard     # Dashboard stats

GET    /api/v1/health                # Health check
```

---

## 🧪 Testing Strategy

### Backend Tests
```bash
cd backend
pytest tests/
pytest tests/ --cov=app  # with coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Tests
- Test complete podcast generation flow
- Test API endpoints with real database
- Test error handling and edge cases

---

## 📦 Deployment Checklist

- [ ] Set up production PostgreSQL
- [ ] Configure environment variables
- [ ] Set up S3 or file storage
- [ ] Configure domain and SSL
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure logging
- [ ] Set up CI/CD pipeline
- [ ] Load testing
- [ ] Security audit
- [ ] Documentation

---

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/tutorial/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **React + TypeScript**: https://react-typescript-cheatsheet.netlify.app/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **OpenAI API**: https://platform.openai.com/docs/guides/gpt
- **ElevenLabs**: https://elevenlabs.io/docs/api-reference

---

## 💡 Tips for Success

1. **Start Small**: Implement one feature at a time
2. **Test Early**: Write tests as you build
3. **Use Type Hints**: Leverage Python type hints and TypeScript
4. **Document Code**: Add docstrings and comments
5. **Version Control**: Commit frequently with clear messages
6. **Monitor Costs**: Track API usage for OpenAI and ElevenLabs
7. **Handle Errors**: Implement proper error handling and logging
8. **Optimize Later**: Get it working first, then optimize

---

## 🐛 Common Issues & Solutions

### Backend
- **Import errors**: Make sure virtual environment is activated
- **Database errors**: Check PostgreSQL is running and credentials are correct
- **API key errors**: Verify `.env` file is in backend directory

### Frontend
- **Module not found**: Run `npm install` again
- **Proxy errors**: Check backend is running on port 8000
- **Build errors**: Clear cache with `rm -rf node_modules package-lock.json && npm install`

### Docker
- **Port conflicts**: Change ports in `docker-compose.yml`
- **Build errors**: Run `docker-compose down -v && docker-compose up --build`

---

## 📞 Support

For questions about the project:
1. Check `README.md` and `SETUP.md`
2. Review API documentation at `http://localhost:8000/docs`
3. Check error logs in terminal

---

## ✅ Project Status Summary

**Completed:**
- ✅ Complete directory structure
- ✅ Backend configuration (FastAPI, SQLAlchemy, Alembic)
- ✅ Frontend configuration (React, TypeScript, Vite, Tailwind)
- ✅ Database models (User, Podcast, Metrics)
- ✅ Docker setup
- ✅ Documentation (README, SETUP, PROJECT_OVERVIEW)
- ✅ Git configuration (.gitignore)

**Ready for Implementation:**
- 🚀 API services (Firecrawl, OpenAI, ElevenLabs)
- 🚀 API endpoints
- 🚀 Frontend pages and components
- 🚀 Background task processing
- 🚀 Authentication system
- 🚀 Testing suite

---

**Last Updated**: May 4, 2026
**Project**: Personal Podcast Generator - Prosper AI Hiring Project
**Status**: Structure Complete - Ready for Development
