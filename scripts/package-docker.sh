#!/bin/bash
# DNDStoryTelling Docker Packaging Script
# Creates production-ready Docker packages for deployment

set -e

# Default configuration
IMAGE_TAG="production-v1.0.0"
OUTPUT_DIR="./docker-packages"
BUILD_TYPE="production"
COMPRESS=true
VERBOSE=false

# Color output functions
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_info() { echo -e "\033[36mℹ️ $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️ $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_step() { echo -e "\033[34m🔄 $1\033[0m"; }

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --build-type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --tag TAG              Docker image tag (default: production-v1.0.0)"
            echo "  --output-dir DIR       Output directory (default: ./docker-packages)"
            echo "  --build-type TYPE      Build type: production, development, multi-arch (default: production)"
            echo "  --no-compress          Skip compression of exported image"
            echo "  --verbose              Enable verbose output"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🐳 DNDStoryTelling Docker Packaging Script"
echo "=========================================="
echo ""

# Check Docker availability
print_step "Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker version &> /dev/null; then
    print_error "Docker daemon is not running or not accessible"
    exit 1
fi

DOCKER_VERSION=$(docker version --format '{{.Client.Version}}')
print_success "Docker is available: $DOCKER_VERSION"

# Create output directory
print_step "Creating output directory..."
mkdir -p "$OUTPUT_DIR"
print_success "Output directory ready: $OUTPUT_DIR"

# Set image names and paths
IMAGE_NAME="dndstorytelling"
FULL_IMAGE_TAG="${IMAGE_NAME}:${IMAGE_TAG}"
EXPORT_FILE_NAME="${IMAGE_NAME}-${IMAGE_TAG}.tar"
EXPORT_PATH="${OUTPUT_DIR}/${EXPORT_FILE_NAME}"

# Choose Dockerfile and build parameters
DOCKERFILE_PATH="."
BUILD_ARGS=()

case $BUILD_TYPE in
    "production")
        DOCKERFILE_PATH="Dockerfile.prod"
        BUILD_ARGS+=("--build-arg" "ENVIRONMENT=production")
        print_info "Building production image with security hardening"
        ;;
    "development")
        DOCKERFILE_PATH="Dockerfile"
        BUILD_ARGS+=("--build-arg" "ENVIRONMENT=development")
        print_info "Building development image with debug features"
        ;;
    "multi-arch")
        DOCKERFILE_PATH="Dockerfile.prod"
        BUILD_ARGS+=("--platform" "linux/amd64,linux/arm64")
        print_info "Building multi-architecture image (AMD64 + ARM64)"
        ;;
    *)
        print_error "Invalid build type: $BUILD_TYPE"
        exit 1
        ;;
esac

# Build the Docker image
print_step "Building Docker image: $FULL_IMAGE_TAG"
print_info "Using Dockerfile: $DOCKERFILE_PATH"

BUILD_CMD=(
    docker build
    -f "$DOCKERFILE_PATH"
    -t "$FULL_IMAGE_TAG"
    --build-arg "PIP_DEFAULT_TIMEOUT=300"
    --build-arg "PIP_RETRIES=5"
    "${BUILD_ARGS[@]}"
    .
)

if $VERBOSE; then
    print_info "Build command: ${BUILD_CMD[*]}"
fi

if "${BUILD_CMD[@]}"; then
    print_success "Docker image built successfully: $FULL_IMAGE_TAG"
else
    print_error "Docker build failed"
    exit 1
fi

# Get image information
print_step "Analyzing built image..."
IMAGE_SIZE=$(docker images "$FULL_IMAGE_TAG" --format "{{.Size}}")
print_success "Image built - Size: $IMAGE_SIZE"

# Export the image
print_step "Exporting Docker image to: $EXPORT_PATH"
if docker save -o "$EXPORT_PATH" "$FULL_IMAGE_TAG"; then
    EXPORT_SIZE=$(du -h "$EXPORT_PATH" | cut -f1)
    print_success "Image exported successfully: $EXPORT_PATH ($EXPORT_SIZE)"
else
    print_error "Failed to export image"
    exit 1
fi

# Compress the image if requested
if $COMPRESS; then
    print_step "Compressing exported image..."
    COMPRESSED_PATH="${EXPORT_PATH}.gz"

    if gzip -c "$EXPORT_PATH" > "$COMPRESSED_PATH"; then
        ORIGINAL_SIZE=$(du -h "$EXPORT_PATH" | cut -f1)
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_PATH" | cut -f1)
        print_success "Image compressed: $COMPRESSED_PATH ($COMPRESSED_SIZE)"
        print_info "Original size: $ORIGINAL_SIZE, Compressed size: $COMPRESSED_SIZE"

        echo -n "Remove uncompressed file? (y/N): "
        read -r response
        if [[ "$response" == "y" || "$response" == "Y" ]]; then
            rm "$EXPORT_PATH"
            print_info "Removed uncompressed file"
        fi
    else
        print_warning "Compression failed"
    fi
fi

# Generate deployment files
print_step "Generating deployment files..."
DEPLOYMENT_DIR="${OUTPUT_DIR}/deployment-files"
mkdir -p "$DEPLOYMENT_DIR"

# Copy essential deployment files
DEPLOYMENT_FILES=(
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "docker-compose.synology.yml"
    ".env.example"
    "NAS-DEPLOYMENT.md"
    "DEPLOYMENT.md"
    "README.md"
)

for file in "${DEPLOYMENT_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        cp "$file" "$DEPLOYMENT_DIR/"
        print_info "Copied: $file"
    fi
done

# Create deployment instructions
cat > "${OUTPUT_DIR}/DEPLOYMENT-INSTRUCTIONS.md" << EOF
# DNDStoryTelling Docker Deployment Package

## Package Contents
- Docker Image: $EXPORT_FILE_NAME$(if $COMPRESS; then echo ".gz"; fi)
- Deployment Files: deployment-files/
- This README

## Quick Deployment

### 1. Load Docker Image
\`\`\`bash
$(if $COMPRESS; then echo "# If compressed"; echo "gunzip $EXPORT_FILE_NAME.gz"; fi)
docker load < $EXPORT_FILE_NAME
\`\`\`

### 2. Verify Image
\`\`\`bash
docker images | grep dndstorytelling
\`\`\`

### 3. Deploy
\`\`\`bash
# Copy docker-compose files from deployment-files/
cp deployment-files/docker-compose.prod.yml .
cp deployment-files/.env.example .env

# Edit .env with your settings
# Then deploy
docker-compose -f docker-compose.prod.yml up -d
\`\`\`

## Image Details
- **Image**: $FULL_IMAGE_TAG
- **Build Type**: $BUILD_TYPE
- **Built**: $(date '+%Y-%m-%d %H:%M:%S')
- **Architecture**: $(if [[ "$BUILD_TYPE" == "multi-arch" ]]; then echo "linux/amd64, linux/arm64"; else echo "linux/amd64"; fi)

## Deployment Guides
See deployment-files/ for complete guides:
- NAS-DEPLOYMENT.md - Synology, QNAP, TrueNAS deployment
- DEPLOYMENT.md - Production deployment guide
- README.md - Application overview and configuration

## Support
For issues or questions, see the GitHub repository or deployment guides.
EOF

print_success "Generated deployment instructions"

# Final summary
echo ""
echo "🎉 Docker Packaging Complete!"
echo "=============================="
echo ""
print_info "📦 Package Location: $OUTPUT_DIR"
print_info "🐳 Docker Image: $FULL_IMAGE_TAG"
print_info "📁 Export File: $EXPORT_FILE_NAME$(if $COMPRESS; then echo '.gz'; fi)"
print_info "📋 Deployment Files: deployment-files/"
echo ""
echo "🚀 Next Steps:"
echo "1. Transfer the package to your target system"
echo "2. Follow DEPLOYMENT-INSTRUCTIONS.md"
echo "3. Load the image: docker load < $EXPORT_FILE_NAME$(if $COMPRESS; then echo '.gz (after gunzip)'; fi)"
echo "4. Deploy using the provided docker-compose files"
echo ""

# Cleanup option
echo -n "Clean up build image from local Docker? (y/N): "
read -r response
if [[ "$response" == "y" || "$response" == "Y" ]]; then
    docker rmi "$FULL_IMAGE_TAG"
    print_info "Removed local build image"
fi

print_success "Packaging script completed successfully!"