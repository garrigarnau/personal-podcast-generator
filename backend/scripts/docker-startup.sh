#!/bin/bash
set -e

echo "================================================"
echo "Personal Podcast Generator - Backend Startup"
echo "================================================"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to wait for postgres
wait_for_postgres() {
    echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"

    max_retries=30
    retry_count=0

    until pg_isready -h "${POSTGRES_HOST:-db}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-podcast_user}" > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))

        if [ $retry_count -ge $max_retries ]; then
            echo -e "${RED}PostgreSQL did not become ready in time. Exiting.${NC}"
            exit 1
        fi

        echo -e "${YELLOW}PostgreSQL is unavailable - sleeping (attempt $retry_count/$max_retries)${NC}"
        sleep 2
    done

    echo -e "${GREEN}PostgreSQL is ready!${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"

    if alembic upgrade head; then
        echo -e "${GREEN}Database migrations completed successfully!${NC}"
    else
        echo -e "${RED}Database migration failed. Exiting.${NC}"
        exit 1
    fi
}

# Function to create initial data (optional)
create_initial_data() {
    echo -e "${YELLOW}Checking for initial data setup...${NC}"

    # You can add Python script here to create initial admin users, etc.
    # python -m app.db_init

    echo -e "${GREEN}Initial data check complete!${NC}"
}

# Main startup sequence
main() {
    echo -e "${YELLOW}Starting backend service...${NC}"

    # Wait for database
    wait_for_postgres

    # Run migrations
    run_migrations

    # Create initial data (if needed)
    # create_initial_data

    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Backend startup complete! Starting uvicorn...${NC}"
    echo -e "${GREEN}================================================${NC}"

    # Start the application
    # Production mode with multiple workers
    if [ "${ENVIRONMENT:-production}" = "production" ]; then
        echo -e "${GREEN}Starting in PRODUCTION mode with 4 workers${NC}"
        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 4 \
            --log-level info
    else
        # Development mode with auto-reload
        echo -e "${YELLOW}Starting in DEVELOPMENT mode with hot-reload${NC}"
        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --reload \
            --log-level debug
    fi
}

# Run main function
main
