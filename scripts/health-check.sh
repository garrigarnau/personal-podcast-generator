#!/bin/bash
# ==============================================================================
# Personal Podcast Generator - Health Check Script
# ==============================================================================
# Comprehensive health check for all services

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-podcast_user}"
DB_NAME="${DB_NAME:-podcast_db}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Personal Podcast Generator - Health Check${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Track overall health
OVERALL_HEALTH=0

# Function to check service
check_service() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Checking $name... "

    if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null); then
        if [ "$response" = "$expected" ]; then
            echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected)"
            OVERALL_HEALTH=1
            return 1
        fi
    else
        echo -e "${RED}✗ UNREACHABLE${NC}"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check JSON endpoint
check_json_endpoint() {
    local name=$1
    local url=$2
    local field=$3
    local expected=$4

    echo -n "Checking $name... "

    if response=$(curl -s --max-time 5 "$url" 2>/dev/null); then
        if [ -n "$response" ]; then
            if value=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$field', ''))" 2>/dev/null); then
                if [ "$value" = "$expected" ]; then
                    echo -e "${GREEN}✓ OK${NC} ($field: $value)"
                    return 0
                else
                    echo -e "${YELLOW}⚠ WARNING${NC} ($field: $value, expected $expected)"
                    return 0
                fi
            fi
        fi
    fi

    echo -e "${RED}✗ FAIL${NC}"
    OVERALL_HEALTH=1
    return 1
}

# Function to check database
check_database() {
    echo -n "Checking database... "

    if docker-compose exec -T db pg_isready -h localhost -p 5432 -U "$DB_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC} (PostgreSQL accepting connections)"

        # Check database size
        if size=$(docker-compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs); then
            echo "  Database size: $size"
        fi

        # Check table counts
        if count=$(docker-compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM podcasts;" 2>/dev/null | xargs); then
            echo "  Total podcasts: $count"
        fi

        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    echo -n "Checking disk space... "

    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    local available=$(df -h / | awk 'NR==2 {print $4}')

    if [ "$usage" -lt 80 ]; then
        echo -e "${GREEN}✓ OK${NC} ($usage% used, $available available)"
        return 0
    elif [ "$usage" -lt 90 ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} ($usage% used, $available available)"
        return 0
    else
        echo -e "${RED}✗ CRITICAL${NC} ($usage% used, $available available)"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check Docker containers
check_containers() {
    echo -n "Checking Docker containers... "

    local running=$(docker-compose ps --services --filter "status=running" | wc -l | xargs)
    local expected=3

    if [ "$running" -eq "$expected" ]; then
        echo -e "${GREEN}✓ OK${NC} ($running/$expected containers running)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} ($running/$expected containers running)"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check Docker volumes
check_volumes() {
    echo -n "Checking Docker volumes... "

    local volumes=$(docker volume ls --filter "name=personal-podcast-generator" --format "{{.Name}}" | wc -l | xargs)

    if [ "$volumes" -ge 3 ]; then
        echo -e "${GREEN}✓ OK${NC} ($volumes volumes found)"
        return 0
    else
        echo -e "${YELLOW}⚠ WARNING${NC} ($volumes volumes found, expected at least 3)"
        return 0
    fi
}

# Run health checks
echo -e "${YELLOW}Service Health:${NC}"
check_service "Frontend" "$FRONTEND_URL/health" "200"
check_json_endpoint "Backend Health" "$BACKEND_URL/health" "status" "healthy"
check_json_endpoint "Backend API" "$BACKEND_URL/" "status" "running"
check_database

echo ""
echo -e "${YELLOW}System Health:${NC}"
check_disk_space
check_containers
check_volumes

echo ""
echo -e "${YELLOW}Container Status:${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}Volume Usage:${NC}"
docker system df -v | grep personal-podcast-generator | head -n 10 || echo "No volumes found"

echo ""
echo -e "${YELLOW}Recent Logs (last 5 lines per service):${NC}"
echo -e "${BLUE}Backend:${NC}"
docker-compose logs --tail=5 backend 2>/dev/null || echo "No logs available"
echo -e "${BLUE}Frontend:${NC}"
docker-compose logs --tail=5 frontend 2>/dev/null || echo "No logs available"
echo -e "${BLUE}Database:${NC}"
docker-compose logs --tail=5 db 2>/dev/null || echo "No logs available"

# Summary
echo ""
echo -e "${BLUE}================================================${NC}"
if [ $OVERALL_HEALTH -eq 0 ]; then
    echo -e "${GREEN}✓ All health checks passed!${NC}"
    echo -e "${BLUE}================================================${NC}"
    exit 0
else
    echo -e "${RED}✗ Some health checks failed!${NC}"
    echo -e "${YELLOW}Check the output above for details.${NC}"
    echo -e "${BLUE}================================================${NC}"
    exit 1
fi
