# Project Setup Guide

Complete setup instructions for local development and Docker deployment.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (20+ recommended)
- **PostgreSQL 15+**
- **FFmpeg** (required for audio processing)
- **API Keys:**
  - OpenAI (https://platform.openai.com/api-keys)
  - ElevenLabs (https://elevenlabs.io/)
  - Firecrawl (https://www.firecrawl.dev/)
  - News API (https://newsapi.org/)

## Quick Start

### Backend Setup

1. **Create and activate virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. **Initialize database:**
```bash
# Make sure PostgreSQL is running
# Note: alembic.ini contains hardcoded database URL
# If using different credentials, update line 61 in backend/alembic.ini
alembic upgrade head
```

5. **Start the backend server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env
# Default API URL: VITE_API_BASE_URL=http://localhost:8000
```

3. **Start the development server:**
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### Docker Setup (Alternative)

If you prefer using Docker:

```bash
# 1. Copy environment file
cp .env.docker.example .env

# 2. Edit .env and add your API keys
nano .env  # or use your preferred editor

# 3. Start all services
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000
- Frontend app on port **3000** (not 5173 - that's for local dev)

**See [DOCKER_README.md](DOCKER_README.md) for comprehensive Docker documentation.**

## Project Structure

```
personal-podcast-generator/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Configuration & utilities
│   │   │   └── config.py        # Settings management
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic
│   │   └── main.py              # Application entry point
│   ├── alembic/                 # Database migrations
│   │   ├── versions/            # Migration files
│   │   └── env.py               # Alembic configuration
│   ├── requirements.txt         # Python dependencies
│   ├── alembic.ini             # Alembic settings
│   └── .env.example            # Environment template
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/         # Reusable components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client
│   │   ├── types/              # TypeScript types
│   │   ├── App.tsx             # Root component
│   │   ├── main.tsx            # Entry point
│   │   └── index.css           # Global styles (Tailwind)
│   ├── package.json            # Node dependencies
│   ├── tsconfig.json           # TypeScript config
│   ├── vite.config.ts          # Vite configuration
│   ├── tailwind.config.js      # Tailwind CSS config
│   └── index.html              # HTML template
│
├── docker-compose.yml          # Docker orchestration
├── .gitignore                  # Git ignore rules
└── README.md                   # Project documentation
```

## Technology Stack

### Backend
- **FastAPI 0.115.0** - Modern, high-performance web framework
- **SQLAlchemy 2.0.36** - SQL toolkit and ORM
- **PostgreSQL** - Relational database
- **Alembic 1.14.0** - Database migrations
- **Pydantic 2.9.2** - Data validation
- **OpenAI 1.54.3** - Content analysis and script generation
- **ElevenLabs 1.10.0** - Text-to-speech synthesis
- **Firecrawl 4.24.0** - Web scraping and content extraction
- **News API** - Article discovery service
- **LangChain** - Multi-agent orchestration
- **pydub 0.25.1** - Audio processing (requires FFmpeg)
- **python-jose** - JWT authentication
- **bcrypt** - Password hashing

### Frontend
- **React 18.3** - UI library
- **TypeScript 5.6** - Type-safe JavaScript
- **Vite 5.4** - Fast build tool
- **Tailwind CSS 3.4** - Utility-first CSS
- **React Router 6.28** - Client-side routing
- **Recharts 2.13** - Data visualization
- **Lucide React 0.462** - Icon library
- **Axios 1.7** - HTTP client

## Environment Variables

### Backend Environment (backend/.env)

Create a `.env` file in the `backend` directory with the following:

```env
# Database
DATABASE_URL=postgresql+asyncpg://podcast_user:podcast_password@localhost:5432/podcast_db

# API Keys (ALL REQUIRED - get these from respective services)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...
NEWS_API_KEY=...                         # REQUIRED - from newsapi.org

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-this   # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080        # 7 days

# Application
ENVIRONMENT=development
DEBUG=True
SQL_ECHO=False                           # Set to True to log SQL queries

# LangSmith (Optional - for AI call tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=                       # Optional
LANGSMITH_PROJECT=personal-podcast
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# News API
NEWS_API_BASE_URL=https://newsapi.org/v2
```

### Frontend Environment (frontend/.env)

Create a `.env` file in the `frontend` directory:

```env
# API Base URL
VITE_API_BASE_URL=http://localhost:8000  # Backend API endpoint
```

### Docker Environment (.env at project root)

For Docker deployments, use `.env.docker.example` as a template:

```bash
cp .env.docker.example .env
# Edit and add all required API keys
```

## API Documentation

Once the backend is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Workflow

1. **Backend Changes:**
   - Add/modify models in `backend/app/models/`
   - Create migrations: `alembic revision --autogenerate -m "description"`
   - Apply migrations: `alembic upgrade head`
   - Add business logic in `backend/app/services/`
   - Create API endpoints in `backend/app/api/`

2. **Frontend Changes:**
   - Add components in `frontend/src/components/`
   - Define types in `frontend/src/types/`
   - Create API services in `frontend/src/services/`
   - Add pages in `frontend/src/pages/`

3. **Testing:**
   - Backend: Tests in development - run with `pytest` when available
   - Frontend: Tests in development - use `npm run lint` for code quality

## Next Steps

1. **Database Models:** Define your database schema in `backend/app/models/`
2. **API Endpoints:** Implement REST API in `backend/app/api/`
3. **Services:** Add business logic for:
   - Web scraping (Firecrawl)
   - Content analysis (OpenAI)
   - Audio generation (ElevenLabs)
4. **Frontend Pages:** Build UI for:
   - URL input and podcast generation
   - Podcast library/history
   - Analytics dashboard
5. **Authentication:** Implement user authentication
6. **Deployment:** Configure for production deployment

## Troubleshooting

### Backend Issues
- **Database connection errors:**
  - Check PostgreSQL is running: `pg_isready`
  - Verify credentials in `.env` match your PostgreSQL setup
  - Update `backend/alembic.ini` line 61 if using different credentials
- **Import errors:** Ensure virtual environment is activated
- **API key errors:** Verify all API keys (including NEWS_API_KEY) are set in `.env`
- **Missing NEWS_API_KEY:** This is required - get free key from https://newsapi.org/
- **FFmpeg not found:** Install FFmpeg for audio processing (required by pydub)

### Frontend Issues
- **Port already in use:** Change port in `vite.config.ts` or kill process using port 5173
- **Module not found:** Run `npm install` again
- **TypeScript errors:** Check `tsconfig.json` configuration
- **API connection failed:** Verify VITE_API_BASE_URL in `frontend/.env` points to backend
- **npm test not found:** Tests are in development - use `npm run lint` instead

### Docker Issues
- **Containers won't start:**
  - Check logs: `docker-compose logs backend`
  - Verify all required API keys are in `.env` (including NEWS_API_KEY)
  - Ensure `.env` file exists: `cp .env.docker.example .env`
- **Port conflicts:**
  - Frontend runs on port 3000 in Docker (not 5173)
  - Change ports in `.env`: FRONTEND_PORT, BACKEND_PORT, POSTGRES_PORT
- **Database not ready:** Wait for health check to pass (check with `docker-compose ps`)
- **Missing .env file:** Copy `.env.docker.example` to `.env` before running docker-compose

## Additional Documentation

- **[README.md](README.md)** - Project overview and features
- **[WORKFLOW.md](WORKFLOW.md)** - Detailed workflow from news to audio
- **[DOCKER_README.md](DOCKER_README.md)** - Docker quick reference
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Comprehensive Docker guide

## External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [Firecrawl Documentation](https://www.firecrawl.dev/)
- [News API Documentation](https://newsapi.org/docs)

## Security Notes

1. **Never commit .env files** - they contain sensitive API keys
2. **Change SECRET_KEY in production** - generate with `openssl rand -hex 32`
3. **Use strong PostgreSQL passwords** in production
4. **Rotate API keys regularly** for security
5. **Enable HTTPS** in production deployments
