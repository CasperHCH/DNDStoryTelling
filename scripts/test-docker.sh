#!/bin/bash
# Docker test runner script

set -e

echo "🐳 Starting Docker-based test environment..."

# Build the test image
echo "📦 Building test image..."
docker-compose -f docker-compose.test.yml build test

# Start the test database
echo "🗄️ Starting test database..."
docker-compose -f docker-compose.test.yml up -d test_db

# Wait for database to be ready
echo "⏳ Waiting for test database to be ready..."
docker-compose -f docker-compose.test.yml exec -T test_db bash -c '
  until pg_isready -U test_user -d dndstory_test; do
    echo "Waiting for PostgreSQL..."
    sleep 2
  done
  echo "PostgreSQL is ready!"
'

# Run database migrations for test
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.test.yml run --rm test alembic upgrade head

# Run the tests
echo "🧪 Running tests..."
docker-compose -f docker-compose.test.yml run --rm test

# Cleanup
echo "🧹 Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

echo "✅ Tests completed!"