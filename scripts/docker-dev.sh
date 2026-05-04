#!/bin/bash
# ==============================================================================
# Personal Podcast Generator - Development Mode Script
# ==============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Personal Podcast Generator - Development Mode${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found!${NC}"
    echo -e "${YELLOW}Copying .env.docker.example to .env...${NC}"
    cp .env.docker.example .env
    echo -e "${RED}Please edit .env and add your API keys before continuing!${NC}"
    exit 1
fi

# Override for development
export ENVIRONMENT=development
export DEBUG=True

echo -e "${YELLOW}Starting in DEVELOPMENT mode with hot-reload...${NC}"

# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Note: This will keep running until Ctrl+C
