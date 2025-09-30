#!/bin/bash

# UI Test Startup Script
# This script starts the application for UI testing

set -e

echo "Starting D&D Story Telling application for UI tests..."

# Set test environment variables
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://user:password@localhost:5432/dndstory_test}"
export SECRET_KEY="${SECRET_KEY:-test_secret_key}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-test_openai_key}"
export CONFLUENCE_API_TOKEN="${CONFLUENCE_API_TOKEN:-test_confluence_token}"
export CONFLUENCE_URL="${CONFLUENCE_URL:-https://test.atlassian.net}"
export PYTHONPATH="${PYTHONPATH:-.}"

# Function to check if server is running
check_server() {
    curl -s http://localhost:8000 > /dev/null 2>&1
    return $?
}

# Function to wait for server
wait_for_server() {
    local timeout=30
    local count=0
    
    echo "Waiting for server to start..."
    
    while ! check_server; do
        if [ $count -ge $timeout ]; then
            echo "ERROR: Server failed to start within $timeout seconds"
            return 1
        fi
        
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    echo ""
    echo "Server is running and responding!"
    return 0
}

# Start the server
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for the server to be ready
if wait_for_server; then
    echo "Server started successfully with PID: $SERVER_PID"
    echo "Application is ready for UI testing at http://localhost:8000"
else
    echo "Failed to start server"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Keep the script running if called directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "Press Ctrl+C to stop the server"
    trap "kill $SERVER_PID 2>/dev/null || true; exit 0" INT TERM
    wait $SERVER_PID
fi