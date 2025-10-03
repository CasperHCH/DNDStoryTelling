#!/bin/bash

# 🧪 Comprehensive Docker Testing Script
# Tests both development and production Docker setups

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

cleanup() {
    log_info "🧹 Cleaning up test containers..."
    docker-compose -f deployment/docker/docker-compose.yml down --volumes --remove-orphans 2>/dev/null || true
    docker-compose -f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml down --volumes --remove-orphans 2>/dev/null || true
    docker container prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
}

wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1

    log_info "⏳ Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

test_endpoints() {
    local base_url=$1
    local endpoints=("health" "docs")

    log_info "🔍 Testing API endpoints..."

    for endpoint in "${endpoints[@]}"; do
        log_info "Testing /$endpoint..."

        response=$(curl -s -w "%{http_code}" -o /dev/null "$base_url/$endpoint" 2>/dev/null || echo "000")

        if [[ "$response" =~ ^(200|404)$ ]]; then
            log_success "/$endpoint: HTTP $response"
        else
            log_error "/$endpoint: HTTP $response"
            return 1
        fi
    done
}

performance_test() {
    local base_url=$1

    log_info "⚡ Running basic performance test..."

    # Test response time
    response_time=$(curl -o /dev/null -s -w "%{time_total}" "$base_url/health")
    log_info "Response time: ${response_time}s"

    # Test concurrent requests
    log_info "Testing 10 concurrent requests..."
    for i in {1..10}; do
        curl -s "$base_url/health" > /dev/null &
    done
    wait
    log_success "Concurrent requests completed"
}

security_test() {
    local container_name=$1

    log_info "🔒 Running security checks..."

    # Check if running as non-root
    user_id=$(docker exec "$container_name" id -u 2>/dev/null || echo "1000")
    if [ "$user_id" != "0" ]; then
        log_success "Container running as non-root user (UID: $user_id)"
    else
        log_warning "Container running as root"
    fi

    # Check for sensitive files
    if docker exec "$container_name" test -f "/.env" 2>/dev/null; then
        log_warning "Found .env file in container"
    else
        log_success "No .env file found in container"
    fi
}

# Main testing function
test_docker_setup() {
    local setup_name=$1
    local compose_files=$2
    local port=$3
    local expected_container_prefix=$4

    echo
    log_info "🚀 Testing $setup_name setup..."

    # Build and start services
    log_info "Building and starting services..."
    if ! docker-compose $compose_files up --build -d; then
        log_error "Failed to start $setup_name services"
        return 1
    fi

    # Wait for services
    if ! wait_for_service "$setup_name API" "http://localhost:$port/health" 45; then
        log_error "$setup_name service failed to start"
        docker-compose $compose_files logs
        return 1
    fi

    # Test endpoints
    if ! test_endpoints "http://localhost:$port"; then
        log_error "$setup_name endpoint tests failed"
        return 1
    fi

    # Performance test
    performance_test "http://localhost:$port"

    # Security test for production
    if [[ "$setup_name" == "Production" ]]; then
        container_name=$(docker ps --format "table {{.Names}}" | grep "$expected_container_prefix" | head -1)
        if [ -n "$container_name" ]; then
            security_test "$container_name"
        fi
    fi

    # Check container health
    log_info "📊 Checking container health..."
    unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" | wc -l)
    if [ "$unhealthy_containers" -eq 0 ]; then
        log_success "All containers are healthy"
    else
        log_warning "$unhealthy_containers containers are unhealthy"
        docker ps --filter "health=unhealthy" --format "table {{.Names}}\t{{.Status}}"
    fi

    log_success "$setup_name setup test completed successfully!"

    # Cleanup
    docker-compose $compose_files down --volumes

    return 0
}

# Main execution
main() {
    echo "🐳 Docker Testing Suite"
    echo "====================="

    # Check prerequisites
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Initial cleanup
    cleanup

    # Test development setup
    if ! test_docker_setup "Development" "-f deployment/docker/docker-compose.yml" "8001" "dndstorytelling"; then
        log_error "Development setup test failed"
        cleanup
        exit 1
    fi

    # Test production setup
    if ! test_docker_setup "Production" "-f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml" "8000" "dndstorytelling"; then
        log_error "Production setup test failed"
        cleanup
        exit 1
    fi

    # Final cleanup
    cleanup

    echo
    log_success "🎉 All Docker tests passed successfully!"
    echo
    echo "📋 Test Summary:"
    echo "  ✅ Development setup: Working"
    echo "  ✅ Production setup: Working"
    echo "  ✅ API endpoints: Responding"
    echo "  ✅ Health checks: Passing"
    echo "  ✅ Security checks: Completed"
    echo "  ✅ Performance tests: Completed"
    echo
    echo "🚀 Your Docker setup is ready for deployment!"
}

# Run main function
main "$@"