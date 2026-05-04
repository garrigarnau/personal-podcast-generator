# Project Setup Guide

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

2. **Start the development server:**
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### Docker Setup (Alternative)

If you prefer using Docker:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000
- Frontend app on port 5173

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
- **Firecrawl 1.5.1** - Web scraping and content extraction

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

Create a `.env` file in the `backend` directory with the following:

```env
# Database
DATABASE_URL=postgresql://podcast_user:podcast_password@localhost:5432/podcast_db

# API Keys (get these from respective services)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...

# Application
ENVIRONMENT=development
DEBUG=True
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
   - Backend: Add tests and run with `pytest`
   - Frontend: Add tests and run with `npm test`

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
- **Database connection errors:** Check PostgreSQL is running and credentials are correct
- **Import errors:** Ensure virtual environment is activated
- **API key errors:** Verify all API keys are set in `.env`

### Frontend Issues
- **Port already in use:** Change port in `vite.config.ts`
- **Module not found:** Run `npm install` again
- **TypeScript errors:** Check `tsconfig.json` configuration

### Docker Issues
- **Containers won't start:** Check logs with `docker-compose logs`
- **Port conflicts:** Change ports in `docker-compose.yml`
- **Database not ready:** Wait for health check to pass

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [Firecrawl Documentation](https://www.firecrawl.dev/)
