#!/bin/bash
# ==============================================================================
# Personal Podcast Generator - Production Deployment Script
# ==============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Personal Podcast Generator - Production Deploy${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.docker.example to .env and configure your API keys:${NC}"
    echo -e "  cp .env.docker.example .env"
    echo -e "  # Then edit .env with your actual API keys"
    exit 1
fi

# Validate required environment variables
echo -e "${YELLOW}Validating environment configuration...${NC}"
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY is not configured in .env${NC}"
    exit 1
fi

if [ -z "$ELEVENLABS_API_KEY" ] || [ "$ELEVENLABS_API_KEY" = "your_elevenlabs_api_key_here" ]; then
    echo -e "${RED}Error: ELEVENLABS_API_KEY is not configured in .env${NC}"
    exit 1
fi

if [ -z "$FIRECRAWL_API_KEY" ] || [ "$FIRECRAWL_API_KEY" = "your_firecrawl_api_key_here" ]; then
    echo -e "${RED}Error: FIRECRAWL_API_KEY is not configured in .env${NC}"
    exit 1
fi

echo -e "${GREEN}Environment validation passed!${NC}"

# Pull latest images (if using pre-built images)
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build --no-cache

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check health status
echo -e "${YELLOW}Checking service health...${NC}"
docker-compose ps

# Show logs
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e ""
echo -e "Services running at:"
echo -e "  - Frontend: ${GREEN}http://localhost:${FRONTEND_PORT:-3000}${NC}"
echo -e "  - Backend API: ${GREEN}http://localhost:${BACKEND_PORT:-8000}${NC}"
echo -e "  - API Docs: ${GREEN}http://localhost:${BACKEND_PORT:-8000}/docs${NC}"
echo -e ""
echo -e "To view logs:"
echo -e "  ${YELLOW}docker-compose logs -f${NC}"
echo -e ""
echo -e "To stop services:"
echo -e "  ${YELLOW}docker-compose down${NC}"
