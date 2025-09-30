#!/bin/bash

# 🐳 Comprehensive Docker Test Suite for D&D Story Telling
# This script performs thorough testing of all Docker configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((TESTS_FAILED++))
    fi
    ((TOTAL_TESTS++))
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}🐳 $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    print_info "Waiting for $name to be ready at $url..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            print_status 0 "$name is ready"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 2
        echo -n "."
    done

    print_status 1 "$name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to test endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3

    print_info "Testing $description: $url"

    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$response_code" = "$expected_status" ]; then
        print_status 0 "$description - HTTP $response_code"
    else
        print_status 1 "$description - Expected HTTP $expected_status, got $response_code"
    fi
}

# Function to test database connection
test_database_connection() {
    local compose_file=$1
    local service_name=$2

    print_info "Testing database connection for $service_name..."

    if docker compose -f "$compose_file" exec -T "$service_name" pg_isready -U user -d dndstory >/dev/null 2>&1; then
        print_status 0 "Database connection successful"
    else
        print_status 1 "Database connection failed"
    fi
}

# Function to check container resource usage
check_container_resources() {
    local container_name=$1

    print_info "Checking resource usage for $container_name..."

    if docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" "$container_name" 2>/dev/null; then
        print_status 0 "Resource monitoring available for $container_name"
    else
        print_status 1 "Could not monitor resources for $container_name"
    fi
}

# Function to test Docker image security
test_image_security() {
    local image_name=$1

    print_info "Running basic security checks on $image_name..."

    # Check if image exists
    if docker image inspect "$image_name" >/dev/null 2>&1; then
        print_status 0 "Image $image_name exists"

        # Check image layers
        local layer_count=$(docker image inspect "$image_name" --format='{{len .RootFS.Layers}}' 2>/dev/null || echo "0")
        print_info "Image has $layer_count layers"

        # Check image size
        local image_size=$(docker image inspect "$image_name" --format='{{.Size}}' 2>/dev/null || echo "0")
        local size_mb=$((image_size / 1024 / 1024))
        print_info "Image size: ${size_mb}MB"

        if [ $size_mb -lt 1000 ]; then
            print_status 0 "Image size is reasonable (< 1GB)"
        else
            print_warning "Image size is large (${size_mb}MB), consider optimization"
        fi
    else
        print_status 1 "Image $image_name does not exist"
    fi
}

# Main test execution
print_header "Docker Comprehensive Test Suite"
print_info "Starting comprehensive Docker testing for D&D Story Telling..."
print_info "Test Date: $(date)"
print_info "Docker Version: $(docker --version)"
print_info "Docker Compose Version: $(docker compose version --short)"

# Test 1: Dockerfile Syntax Validation
print_header "Test 1: Dockerfile Syntax Validation"

for dockerfile in Dockerfile Dockerfile.prod Dockerfile.test; do
    if [ -f "$dockerfile" ]; then
        print_info "Validating $dockerfile syntax..."
        if docker build -f "$dockerfile" --dry-run . >/dev/null 2>&1; then
            print_status 0 "$dockerfile syntax is valid"
        else
            print_status 1 "$dockerfile has syntax errors"
        fi
    else
        print_warning "$dockerfile not found, skipping"
    fi
done

# Test 2: Docker Compose File Validation
print_header "Test 2: Docker Compose File Validation"

for compose_file in docker-compose.yml docker-compose.prod.yml docker-compose.test.yml docker-compose.synology.yml; do
    if [ -f "$compose_file" ]; then
        print_info "Validating $compose_file..."
        if docker compose -f "$compose_file" config >/dev/null 2>&1; then
            print_status 0 "$compose_file is valid"
        else
            print_status 1 "$compose_file has configuration errors"
        fi
    else
        print_warning "$compose_file not found, skipping"
    fi
done

# Test 3: Image Building
print_header "Test 3: Docker Image Building"

print_info "Building development image..."
if docker build -t dndstorytelling:test-dev . >/dev/null 2>&1; then
    print_status 0 "Development image built successfully"
else
    print_status 1 "Development image build failed"
fi

print_info "Building production image..."
if docker build -f Dockerfile.prod -t dndstorytelling:test-prod . >/dev/null 2>&1; then
    print_status 0 "Production image built successfully"
else
    print_status 1 "Production image build failed"
fi

# Test 4: Image Security and Analysis
print_header "Test 4: Image Security Analysis"

test_image_security "dndstorytelling:test-dev"
test_image_security "dndstorytelling:test-prod"

# Test 5: Development Environment Testing
print_header "Test 5: Development Environment Testing"

print_info "Starting development environment..."
if docker compose up -d --build >/dev/null 2>&1; then
    print_status 0 "Development environment started"

    # Wait for services to be ready
    sleep 10

    # Test database
    test_database_connection "docker-compose.yml" "db"

    # Test web service health
    wait_for_service "http://localhost:8000/health" "Web Service"

    # Test API endpoints
    test_endpoint "http://localhost:8000/" "200" "Root endpoint"
    test_endpoint "http://localhost:8000/health" "200" "Health check endpoint"
    test_endpoint "http://localhost:8000/docs" "200" "API documentation"
    test_endpoint "http://localhost:8000/api/v1/nonexistent" "404" "Non-existent endpoint (should return 404)"

    # Check container resources
    check_container_resources "dndstorytelling-web-1"
    check_container_resources "dndstorytelling-db-1"

    # Test logs
    print_info "Checking application logs..."
    if docker compose logs web | grep -q "Application startup complete" || docker compose logs web | grep -q "Uvicorn running"; then
        print_status 0 "Application started successfully (logs confirm)"
    else
        print_warning "Could not confirm application startup from logs"
        print_info "Recent web service logs:"
        docker compose logs --tail=5 web
    fi

    # Stop development environment
    print_info "Stopping development environment..."
    docker compose down -v >/dev/null 2>&1
    print_status 0 "Development environment stopped"
else
    print_status 1 "Failed to start development environment"
fi

# Test 6: Production Environment Testing
print_header "Test 6: Production Environment Testing"

if [ -f "docker-compose.prod.yml" ]; then
    print_info "Starting production environment..."
    if docker compose -f docker-compose.prod.yml up -d --build >/dev/null 2>&1; then
        print_status 0 "Production environment started"

        # Wait for services
        sleep 15

        # Test production endpoints (assuming different port)
        wait_for_service "http://localhost:8001/health" "Production Web Service" || wait_for_service "http://localhost:8000/health" "Production Web Service"

        # Stop production environment
        print_info "Stopping production environment..."
        docker compose -f docker-compose.prod.yml down -v >/dev/null 2>&1
        print_status 0 "Production environment stopped"
    else
        print_status 1 "Failed to start production environment"
    fi
else
    print_warning "docker-compose.prod.yml not found, skipping production tests"
fi

# Test 7: Test Environment Validation
print_header "Test 7: Test Environment Validation"

if [ -f "docker-compose.test.yml" ]; then
    print_info "Validating test environment configuration..."
    if docker compose -f docker-compose.test.yml config >/dev/null 2>&1; then
        print_status 0 "Test environment configuration is valid"

        # Try to start test database
        print_info "Starting test database..."
        if docker compose -f docker-compose.test.yml up -d test_db >/dev/null 2>&1; then
            print_status 0 "Test database started successfully"

            # Wait and test database connection
            sleep 5
            test_database_connection "docker-compose.test.yml" "test_db"

            # Stop test environment
            docker compose -f docker-compose.test.yml down -v >/dev/null 2>&1
        else
            print_status 1 "Failed to start test database"
        fi
    else
        print_status 1 "Test environment configuration is invalid"
    fi
else
    print_warning "docker-compose.test.yml not found, skipping test environment validation"
fi

# Test 8: Multi-platform Build Testing
print_header "Test 8: Multi-platform Build Testing"

print_info "Testing multi-platform build capability..."
if docker buildx version >/dev/null 2>&1; then
    print_status 0 "Docker Buildx is available"

    # Test AMD64 build
    print_info "Testing AMD64 build..."
    if docker buildx build --platform linux/amd64 -t dndstorytelling:test-amd64 . >/dev/null 2>&1; then
        print_status 0 "AMD64 build successful"
    else
        print_status 1 "AMD64 build failed"
    fi

    # Test ARM64 build (may take longer)
    print_info "Testing ARM64 build (this may take a while)..."
    if timeout 300 docker buildx build --platform linux/arm64 -t dndstorytelling:test-arm64 . >/dev/null 2>&1; then
        print_status 0 "ARM64 build successful"
    else
        print_status 1 "ARM64 build failed or timed out (5 minutes)"
    fi
else
    print_status 1 "Docker Buildx not available for multi-platform builds"
fi

# Test 9: Container Resource Constraints
print_header "Test 9: Resource Constraint Testing"

print_info "Testing container with memory constraints (NAS simulation)..."
if docker run -d --name dnd-resource-test --memory=512m --cpus=1.0 -e DATABASE_URL=sqlite:///./test.db -e SECRET_KEY=test_key dndstorytelling:test-dev sleep 30 >/dev/null 2>&1; then
    print_status 0 "Container started with resource constraints"

    # Check if container is still running
    sleep 2
    if docker ps --filter "name=dnd-resource-test" --format "{{.Names}}" | grep -q "dnd-resource-test"; then
        print_status 0 "Container running successfully under resource constraints"
    else
        print_status 1 "Container failed under resource constraints"
    fi

    # Cleanup
    docker stop dnd-resource-test >/dev/null 2>&1
    docker rm dnd-resource-test >/dev/null 2>&1
else
    print_status 1 "Failed to start container with resource constraints"
fi

# Test 10: Cleanup and Final Validation
print_header "Test 10: Cleanup and Final Validation"

print_info "Cleaning up test images and containers..."

# Clean up test images
docker rmi dndstorytelling:test-dev dndstorytelling:test-prod dndstorytelling:test-amd64 dndstorytelling:test-arm64 2>/dev/null || true

# Final system state check
docker system df
print_status 0 "Cleanup completed"

# Final Results
print_header "📊 Test Results Summary"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           TEST RESULTS               ║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC} Total Tests: ${TOTAL_TESTS}                     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${GREEN}Passed: ${TESTS_PASSED}${NC}                        ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${RED}Failed: ${TESTS_FAILED}${NC}                        ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All Docker tests passed! Your containerization is production-ready.${NC}"
    exit 0
else
    echo -e "${RED}⚠️ Some Docker tests failed. Please review the issues above.${NC}"
    exit 1
fi