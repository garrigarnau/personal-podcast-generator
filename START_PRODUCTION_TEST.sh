#!/bin/bash

# Production Mode Test Startup Script
# This script verifies configuration and starts the application in production mode

echo "=================================="
echo "Production Mode Test - Startup"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

echo "📋 Pre-flight Checks"
echo "-----------------------------------"

# Check backend .env file
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅ Backend .env file exists${NC}"

    # Check for API keys
    if grep -q "ELEVENLABS_API_KEY=sk-" backend/.env 2>/dev/null; then
        echo -e "${GREEN}✅ ElevenLabs API key configured${NC}"
    else
        echo -e "${RED}❌ ElevenLabs API key missing or invalid${NC}"
    fi

    if grep -q "OPENAI_API_KEY=sk-" backend/.env 2>/dev/null; then
        echo -e "${GREEN}✅ OpenAI API key configured${NC}"
    else
        echo -e "${RED}❌ OpenAI API key missing or invalid${NC}"
    fi

    if grep -q "FIRECRAWL_API_KEY=fc-" backend/.env 2>/dev/null; then
        echo -e "${GREEN}✅ Firecrawl API key configured${NC}"
    else
        echo -e "${RED}❌ Firecrawl API key missing or invalid${NC}"
    fi
else
    echo -e "${RED}❌ Backend .env file not found${NC}"
    echo "   Create one from backend/.env.example"
    exit 1
fi

# Check if .env exists in root (for Docker)
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Root .env file exists${NC}"
else
    echo -e "${YELLOW}⚠️  Root .env file not found (optional for local dev)${NC}"
fi

# Check Python environment
echo ""
echo "🐍 Python Environment"
echo "-----------------------------------"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check Node environment
echo ""
echo "📦 Node Environment"
echo "-----------------------------------"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node not found${NC}"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm installed: $NPM_VERSION${NC}"
else
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi

# Check PostgreSQL
echo ""
echo "🐘 Database Connection"
echo "-----------------------------------"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL client installed${NC}"

    # Try to connect to database
    PGPASSWORD=podcast_password psql -h localhost -U podcast_user -d podcast_db -c "SELECT 1;" &> /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
    else
        echo -e "${YELLOW}⚠️  Database connection failed (make sure PostgreSQL is running)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  PostgreSQL client not found${NC}"
fi

echo ""
echo "=================================="
echo "Configuration Status"
echo "=================================="
echo ""
echo "Backend Configuration:"
echo "  • Mock Audio: ${GREEN}DISABLED${NC} (real API calls)"
echo "  • Audio Model: eleven_flash_v2_5 (streaming)"
echo "  • Script Model: gpt-4o"
echo ""
echo "Frontend Configuration:"
echo "  • Mock Audio: ${GREEN}DISABLED${NC} (real audio generation)"
echo ""
echo "API Cost per Podcast:"
echo "  • Full Pipeline:     ~\$1.31"
echo "  • Script-to-Audio:   ~\$0.96"
echo ""
echo "=================================="
echo ""

read -p "Ready to start services? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "🚀 Starting Services..."
echo "=================================="

# Start backend in background
echo ""
echo "Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo "   URL: http://localhost:8000"
echo "   Logs: Check terminal output"

# Wait for backend to start
echo ""
echo "Waiting for backend to be ready..."
sleep 3

# Check if backend is responding
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Backend health check failed (may still be starting)${NC}"
fi

# Start frontend
echo ""
echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "   URL: http://localhost:5173 (or check output above)"

echo ""
echo "=================================="
echo "✅ Services Started!"
echo "=================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "📖 Read PRODUCTION_MODE_SETUP.md for testing instructions"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or press Ctrl+C and run:"
echo "  pkill -f uvicorn && pkill -f vite"
echo ""

# Keep script running
echo "Press Ctrl+C to stop all services..."
wait
