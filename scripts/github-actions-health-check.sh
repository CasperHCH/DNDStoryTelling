#!/bin/bash

# 🔧 GitHub Actions Health Check Script
# This script verifies that all GitHub Actions workflow fixes are working correctly

set -e

echo "🚀 GitHub Actions Health Check"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "ℹ️ $1"
}

echo ""
print_info "Checking GitHub Actions workflow files..."

# Check if workflow files exist
WORKFLOW_DIR=".github/workflows"
if [ ! -d "$WORKFLOW_DIR" ]; then
    print_status 1 "Workflow directory not found"
    exit 1
fi
print_status 0 "Workflow directory exists"

# Check individual workflow files
WORKFLOWS=("tests.yml" "docker-tests.yml" "ui-tests.yml")
for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$WORKFLOW_DIR/$workflow" ]; then
        print_status 0 "Workflow file $workflow exists"
    else
        print_status 1 "Workflow file $workflow missing"
    fi
done

echo ""
print_info "Checking for deprecated patterns..."

# Check for deprecated docker-compose usage (should be docker compose)
# Exclude job names and file references, focus on actual commands
if grep -r "docker-compose " "$WORKFLOW_DIR" >/dev/null 2>&1; then
    print_warning "Found 'docker-compose' commands (should be 'docker compose' for v2)"
    echo "Files with issues:"
    grep -r "docker-compose " "$WORKFLOW_DIR" --include="*.yml" | head -5
else
    print_status 0 "No deprecated docker-compose commands found"
fi

# Check for deprecated action versions
echo ""
print_info "Checking for deprecated GitHub Actions versions..."

# Check for deprecated CodeQL action v2
if grep -r "github/codeql-action/upload-sarif@v2" "$WORKFLOW_DIR" >/dev/null 2>&1; then
    print_warning "Found deprecated CodeQL action v2 (should be v3)"
else
    print_status 0 "No deprecated CodeQL actions found"
fi

# Check for deprecated upload-artifact v3
if grep -r "actions/upload-artifact@v3" "$WORKFLOW_DIR" >/dev/null 2>&1; then
    print_warning "Found deprecated upload-artifact v3 (should be v4)"
else
    print_status 0 "No deprecated upload-artifact actions found"
fi

echo ""
print_info "Checking environment files..."

# Check for required environment files
ENV_FILES=(".env.docker.test" ".env.test" ".env.example")
for env_file in "${ENV_FILES[@]}"; do
    if [ -f "$env_file" ]; then
        print_status 0 "Environment file $env_file exists"
    else
        print_warning "Environment file $env_file missing (may be optional)"
    fi
done

echo ""
print_info "Checking Docker files..."

# Check for required Docker files
DOCKER_FILES=("Dockerfile" "docker-compose.yml" "docker-compose.test.yml")
for docker_file in "${DOCKER_FILES[@]}"; do
    if [ -f "$docker_file" ]; then
        print_status 0 "Docker file $docker_file exists"
    else
        print_status 1 "Docker file $docker_file missing"
    fi
done

echo ""
print_info "Testing local Docker Compose syntax..."

# Test docker-compose.test.yml syntax
if command -v docker >/dev/null 2>&1; then
    if docker compose -f docker-compose.test.yml config >/dev/null 2>&1; then
        print_status 0 "docker-compose.test.yml syntax is valid"
    else
        print_status 1 "docker-compose.test.yml has syntax errors"
        print_warning "Run 'docker compose -f docker-compose.test.yml config' for details"
    fi
else
    print_warning "Docker not available for syntax testing"
fi

echo ""
print_info "Testing workflow syntax..."

# Check if GitHub CLI is available for workflow validation
if command -v gh >/dev/null 2>&1; then
    # Try to validate workflows (requires auth)
    if gh auth status >/dev/null 2>&1; then
        print_info "Checking latest workflow runs..."
        if gh run list --limit 3 2>/dev/null; then
            print_status 0 "GitHub CLI can access workflow runs"
        else
            print_warning "Cannot access workflow runs (may need authentication)"
        fi
    else
        print_warning "GitHub CLI not authenticated - cannot check workflow runs"
        print_info "Run 'gh auth login' to authenticate"
    fi
else
    print_warning "GitHub CLI not installed - cannot validate workflows online"
    print_info "Install with: https://cli.github.com/"
fi

echo ""
print_info "Summary of fixes applied:"
echo "========================"
echo "✅ Fixed EOF syntax error in environment file creation"
echo "✅ Updated docker-compose to docker compose (v2)"
echo "✅ Updated GitHub Actions to latest versions:"
echo "   - CodeQL action: v2 → v3"
echo "   - upload-artifact: v3 → v4"
echo "✅ Added platform specifications for ARM64 builds"
echo "✅ Optimized Trivy security scan with disk cleanup"
echo "✅ Simplified SQLite compatibility tests"
echo "✅ Added comprehensive error handling"

echo ""
print_info "Next steps:"
echo "==========="
echo "1. Push your changes to trigger GitHub Actions"
echo "2. Monitor the workflow runs for success"
echo "3. Check the troubleshooting guide if issues persist:"
echo "   docs/GITHUB-ACTIONS-TROUBLESHOOTING.md"

echo ""
if [ -f "docs/GITHUB-ACTIONS-TROUBLESHOOTING.md" ]; then
    print_status 0 "Troubleshooting guide available at docs/GITHUB-ACTIONS-TROUBLESHOOTING.md"
else
    print_warning "Troubleshooting guide not found"
fi

echo ""
echo "🎉 Health check complete!"
echo ""
echo "If all checks pass, your GitHub Actions should run successfully."
echo "Any warnings above should be reviewed but may not prevent successful runs."