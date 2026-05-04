# Personal Podcast Generator

A sophisticated application that transforms web content into engaging, personalized podcasts using AI. Built as part of the Prosper AI hiring process.

## Overview

This application allows users to input URLs or topics, extract and analyze content using AI, and generate natural-sounding podcast episodes with multiple speaker voices. The system provides analytics and insights about generated content.

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM for database management
- **PostgreSQL**: Robust relational database
- **Alembic**: Database migration tool
- **OpenAI**: Content analysis and script generation
- **ElevenLabs**: High-quality text-to-speech conversion
- **Firecrawl**: Web content extraction and scraping

### Frontend
- **React 18**: Modern UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Data visualization for analytics
- **Lucide React**: Beautiful icon library

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
- API Keys for:
  - OpenAI
  - ElevenLabs
  - Firecrawl

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

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Features

- **Content Extraction**: Automatically scrape and extract content from URLs
- **AI-Powered Script Generation**: Transform content into engaging podcast scripts
- **Multi-Voice Synthesis**: Generate natural-sounding audio with multiple speakers
- **Analytics Dashboard**: Track podcast generation metrics and insights
- **User Management**: Secure authentication and user profiles
- **Responsive UI**: Modern, mobile-friendly interface

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Code Quality
- Backend: Follow PEP 8 style guidelines
- Frontend: ESLint configuration included
- Type safety: Leverage TypeScript and Pydantic

### Testing
```bash
# Backend
pytest

# Frontend
npm test
```

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

**For comprehensive Docker documentation, see:**
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Complete setup guide with troubleshooting
- **[DOCKER_README.md](DOCKER_README.md)** - Quick reference

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
