# Personal Podcast Generator

A sophisticated application that transforms web content into engaging, personalized podcasts using AI. Built as part of the Prosper AI hiring process.

## Overview

This application allows users to input URLs or topics, extract and analyze content using AI, and generate natural-sounding podcast episodes with multiple speaker voices. The system provides analytics and insights about generated content.

## Tech Stack

### Backend
- **FastAPI 0.115.0**: Modern async web framework
- **SQLAlchemy 2.0.36**: SQL toolkit and async ORM
- **PostgreSQL 15**: Robust relational database with asyncpg driver
- **Alembic 1.14.0**: Database migration tool
- **Pydantic 2.9.2**: Data validation and settings management
- **OpenAI 1.54.3**: GPT-4o for script generation via LangChain
- **ElevenLabs 1.10.0**: High-quality multi-speaker TTS
- **Firecrawl 4.24.0**: Web content extraction and scraping
- **News API**: Article discovery service
- **LangChain**: Multi-agent orchestration with LangSmith tracing
- **pydub 0.25.1**: Audio processing (requires FFmpeg)
- **python-jose**: JWT authentication
- **bcrypt**: Password hashing

### Frontend
- **React 18.3.1**: Modern UI library
- **TypeScript 5.6.3**: Type-safe JavaScript
- **Vite 5.4.11**: Fast build tool and dev server
- **Tailwind CSS 3.4.15**: Utility-first CSS framework
- **React Router DOM 6.28.0**: Client-side routing
- **Axios 1.7.7**: HTTP client with retry logic
- **Recharts 2.13.3**: Data visualization for analytics
- **Lucide React 0.462.0**: Beautiful icon library

## Project Structure

```
personal-podcast-generator/
├── backend/
│   ├── app/
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic (AI, audio generation, scraping)
│   │   ├── api/          # API endpoints
│   │   └── core/         # Configuration and utilities
│   ├── alembic/          # Database migrations
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client services
│   │   └── types/        # TypeScript type definitions
│   ├── package.json      # Node dependencies
│   └── tsconfig.json     # TypeScript configuration
└── docker-compose.yml    # Container orchestration
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- FFmpeg (for audio processing)
- API Keys for:
  - OpenAI (GPT-4o for script generation)
  - ElevenLabs (text-to-speech)
  - Firecrawl (web scraping)
  - News API (article discovery)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
# Edit the file and add your API keys:
# - OPENAI_API_KEY
# - ELEVENLABS_API_KEY
# - FIRECRAWL_API_KEY
# - NEWS_API_KEY (REQUIRED)
# - SECRET_KEY (change in production!)
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy `.env.example` to `.env` and configure API base URL:
```bash
cp .env.example .env
# Default: VITE_API_BASE_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Features

### Core Functionality
- **Async Podcast Generation**: Background task processing with status polling
- **News Article Discovery**: Automatic article fetching based on user interests
- **AI-Powered Script Generation**: Multi-agent LangChain system with GPT-4o
- **Multi-Speaker Audio**: Natural dialogue between two distinct voices (Alex & Sonia)
- **Custom Script Support**: Generate audio from user-provided scripts
- **Comprehensive Metrics**: Track costs, latency, and resource usage per podcast

### User Features
- **JWT Authentication**: Secure login with 7-day token expiration
- **User Preferences**: Configure interests, podcast tone, and length
- **Schedule Settings**: Set up automatic podcast generation
- **Audio Player**: Full-featured playback with speed control and download
- **Script Viewer**: View podcast scripts with speaker tags and emotions
- **Source Attribution**: See articles used for each podcast

### Admin Features
- **Analytics Dashboard**: KPIs, volume trends, and cost breakdowns
- **Task Monitoring**: Track generation status, duration, and errors
- **Resource Tracking**: Monitor OpenAI tokens, ElevenLabs characters, and Firecrawl usage
- **Health Monitoring**: System status checks and metrics

### Technical Features
- **Async-First Architecture**: Non-blocking I/O for high performance
- **Background Task Management**: Queue-based with concurrency limits
- **Graceful Error Handling**: Retry logic with exponential backoff
- **Real-Time Status Updates**: Frontend polling every 2 seconds
- **Docker Support**: Full containerization with health checks
- **Database Migrations**: Alembic for schema versioning
- **API Documentation**: Interactive Swagger UI and ReDoc

## API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs` - Interactive API testing
- **ReDoc**: `http://localhost:8000/redoc` - Detailed documentation
- **Health Check**: `http://localhost:8000/health` - Service status

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT)
- `GET /api/v1/auth/me` - Get current user info

#### Podcast Generation
- `POST /api/v1/podcasts/generate` - Generate podcast (async, returns 202)
- `POST /api/v1/podcasts/generate-from-script` - Generate audio from script
- `GET /api/v1/podcasts/{id}` - Get podcast details
- `GET /api/v1/podcasts/{id}/status` - Poll podcast status (lightweight)
- `GET /api/v1/podcasts/{id}/audio` - Stream/download audio file
- `GET /api/v1/podcasts/` - List user's podcasts (paginated)

#### User Management
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me/preferences` - Update interests and preferences
- `PUT /api/v1/users/me/schedule` - Configure automatic generation

#### Admin & Analytics
- `GET /api/v1/admin/stats` - Comprehensive system statistics
- `GET /api/v1/admin/podcasts/recent` - Recent podcasts with metrics
- `GET /api/v1/admin/metrics/daily` - Daily aggregated metrics

#### Task Management
- `GET /api/v1/tasks/{task_id}` - Get task status
- `GET /api/v1/tasks/` - List all tasks with statistics
- `POST /api/v1/tasks/{task_id}/cancel` - Cancel running task

See [WORKFLOW.md](WORKFLOW.md) for detailed workflow documentation.

## Environment Variables

### Required Backend Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://podcast_user:password@localhost:5432/podcast_db

# API Keys (ALL REQUIRED)
OPENAI_API_KEY=sk-...                    # OpenAI GPT-4o for script generation
ELEVENLABS_API_KEY=...                   # ElevenLabs for text-to-speech
FIRECRAWL_API_KEY=...                    # Firecrawl for web scraping
NEWS_API_KEY=...                         # News API for article discovery

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-this   # JWT token signing key
ALGORITHM=HS256                          # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=10080        # 7 days
```

### Optional Backend Variables

```bash
# Application Settings
ENVIRONMENT=development                   # development or production
DEBUG=True                                # Enable debug mode
SQL_ECHO=False                            # Log SQL queries

# LangSmith (AI call tracing)
LANGSMITH_TRACING=true                    # Enable tracing
LANGSMITH_API_KEY=...                     # LangSmith API key (optional)
LANGSMITH_PROJECT=personal-podcast        # Project name
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# News API
NEWS_API_BASE_URL=https://newsapi.org/v2  # News API endpoint
```

### Frontend Variables

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000   # Backend API URL
```

### Generating Secure Keys

```bash
# Generate a secure SECRET_KEY
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Development

### Code Quality
- Backend: Follow PEP 8 style guidelines
- Frontend: ESLint configuration included
- Type safety: Leverage TypeScript and Pydantic

### Testing
```bash
# Backend (when tests are implemented)
cd backend
pytest

# Frontend (when tests are implemented)
cd frontend
npm test

# Linting
cd frontend
npm run lint
```

**Note:** Test suite is currently in development.

## Deployment

### Docker Deployment (Recommended)

The easiest way to deploy the Personal Podcast Generator is using Docker:

```bash
# Quick start
cp .env.docker.example .env
nano .env  # Add your API keys
make deploy

# Or use deployment script
./scripts/docker-deploy.sh
```

**Services will be available at:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432 (internal only in production)

**For comprehensive Docker documentation, see:**
- **[DOCKER_README.md](DOCKER_README.md)** - Quick reference guide
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Complete setup guide with troubleshooting
- **[WORKFLOW.md](WORKFLOW.md)** - Detailed workflow from news to audio

### Development with Docker

```bash
# Start with hot-reload
make dev

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production Deployment

For production deployments on AWS, GCP, Azure, or other platforms, see the [DOCKER_SETUP.md](DOCKER_SETUP.md) guide for advanced configuration including:
- Resource limits and scaling
- HTTPS with Let's Encrypt
- Backup and restore procedures
- Monitoring and logging
- CI/CD integration

## License

This project is part of the Prosper AI hiring process.

## Contact

For questions or issues, please contact the development team.
