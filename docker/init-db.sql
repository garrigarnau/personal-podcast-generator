-- PostgreSQL Database Initialization Script
-- Personal Podcast Generator
--
-- This script sets up the initial database configuration
-- Executed automatically when the postgres container starts for the first time

-- Ensure proper encoding and collation
ALTER DATABASE podcast_db SET timezone TO 'UTC';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE podcast_db TO podcast_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete for podcast_db';
    RAISE NOTICE 'User: podcast_user';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm';
END $$;
