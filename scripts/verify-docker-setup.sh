#!/bin/bash
# ==============================================================================
# Personal Podcast Generator - Docker Setup Verification
# ==============================================================================
# Verifies all Docker files are in place and properly configured

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Docker Setup Verification${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

ERRORS=0

# Function to check file exists
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description - MISSING: $file"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check file is executable
check_executable() {
    local file=$1
    local description=$2

    if [ -x "$file" ]; then
        echo -e "${GREEN}✓${NC} $description (executable)"
        return 0
    else
        echo -e "${RED}✗${NC} $description - NOT EXECUTABLE: $file"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    local dir=$1
    local description=$2

    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description - MISSING: $dir"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo -e "${YELLOW}Checking Docker configuration files...${NC}"
check_file "docker-compose.yml" "Main Docker Compose file"
check_file "docker-compose.dev.yml" "Development Docker Compose override"
check_file "docker-compose.prod.yml" "Production Docker Compose override"
check_file ".env.docker.example" "Environment template"
check_file "Makefile" "Makefile for commands"

echo ""
echo -e "${YELLOW}Checking backend Docker files...${NC}"
check_file "backend/Dockerfile" "Backend Dockerfile"
check_file "backend/.dockerignore" "Backend .dockerignore"
check_executable "backend/scripts/docker-startup.sh" "Backend startup script"

echo ""
echo -e "${YELLOW}Checking frontend Docker files...${NC}"
check_file "frontend/Dockerfile" "Frontend Dockerfile"
check_file "frontend/.dockerignore" "Frontend .dockerignore"
check_file "frontend/nginx.conf" "Nginx configuration"

echo ""
echo -e "${YELLOW}Checking database files...${NC}"
check_dir "docker" "Docker directory"
check_file "docker/init-db.sql" "Database initialization script"

echo ""
echo -e "${YELLOW}Checking scripts...${NC}"
check_dir "scripts" "Scripts directory"
check_executable "scripts/docker-deploy.sh" "Production deployment script"
check_executable "scripts/docker-dev.sh" "Development mode script"
check_executable "scripts/health-check.sh" "Health check script"

echo ""
echo -e "${YELLOW}Checking documentation...${NC}"
check_file "DOCKER_SETUP.md" "Comprehensive Docker setup guide"
check_file "DOCKER_README.md" "Docker quick reference"
check_file "DOCKER_FILES_SUMMARY.md" "Docker files summary"

echo ""
echo -e "${YELLOW}Checking CI/CD configuration...${NC}"
check_dir ".github/workflows" "GitHub workflows directory"
check_file ".github/workflows/docker-ci.yml" "GitHub Actions CI/CD workflow"

echo ""
echo -e "${YELLOW}Verifying Docker Compose syntax...${NC}"
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose.yml syntax is valid"
else
    echo -e "${RED}✗${NC} docker-compose.yml has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${YELLOW}Checking Docker availability...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed ($(docker --version))"
else
    echo -e "${RED}✗${NC} Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed ($(docker-compose --version))"
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check for required variables
    if grep -q "OPENAI_API_KEY=" .env; then
        if grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env || grep -q "OPENAI_API_KEY=$" .env; then
            echo -e "${YELLOW}⚠${NC} OPENAI_API_KEY is not configured"
        else
            echo -e "${GREEN}✓${NC} OPENAI_API_KEY is configured"
        fi
    else
        echo -e "${RED}✗${NC} OPENAI_API_KEY is missing in .env"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "ELEVENLABS_API_KEY=" .env; then
        if grep -q "ELEVENLABS_API_KEY=your_elevenlabs_api_key_here" .env || grep -q "ELEVENLABS_API_KEY=$" .env; then
            echo -e "${YELLOW}⚠${NC} ELEVENLABS_API_KEY is not configured"
        else
            echo -e "${GREEN}✓${NC} ELEVENLABS_API_KEY is configured"
        fi
    else
        echo -e "${RED}✗${NC} ELEVENLABS_API_KEY is missing in .env"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "FIRECRAWL_API_KEY=" .env; then
        if grep -q "FIRECRAWL_API_KEY=your_firecrawl_api_key_here" .env || grep -q "FIRECRAWL_API_KEY=$" .env; then
            echo -e "${YELLOW}⚠${NC} FIRECRAWL_API_KEY is not configured"
        else
            echo -e "${GREEN}✓${NC} FIRECRAWL_API_KEY is configured"
        fi
    else
        echo -e "${RED}✗${NC} FIRECRAWL_API_KEY is missing in .env"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file does not exist (copy from .env.docker.example)"
fi

echo ""
echo -e "${YELLOW}Checking Makefile commands...${NC}"
if make -n deploy > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Makefile 'deploy' target is valid"
else
    echo -e "${RED}✗${NC} Makefile 'deploy' target has errors"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${BLUE}================================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
    echo -e "${GREEN}Your Docker setup is complete and ready to use!${NC}"
    echo ""
    echo -e "Next steps:"
    echo -e "  1. Configure your API keys in .env"
    echo -e "  2. Run: ${YELLOW}make deploy${NC}"
    echo -e "  3. Access the app at: ${YELLOW}http://localhost:3000${NC}"
    echo ""
    echo -e "For detailed documentation, see:"
    echo -e "  - DOCKER_SETUP.md (comprehensive guide)"
    echo -e "  - DOCKER_README.md (quick reference)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the errors above before deploying.${NC}"
    echo ""
    exit 1
fi
