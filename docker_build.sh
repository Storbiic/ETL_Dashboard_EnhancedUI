#!/bin/bash

# Docker Multi-Service Build Script
# This script builds frontend and backend Docker images

echo "=========================================="
echo "Docker Multi-Service Build Script"
echo "=========================================="
echo

# Configuration - Edit these variables
FRONTEND_NAME="frontend"
BACKEND_NAME="backend"
IMAGE_TAG="latest"
PROJECT_ROOT="."
FRONTEND_DOCKERFILE="Dockerfile.frontend"
BACKEND_DOCKERFILE="Dockerfile.backend"
PUSH_TO_REGISTRY=false
REGISTRY_USERNAME=""
BUILD_FRONTEND=true
BUILD_BACKEND=true

# Parse command line arguments
while getopts "t:u:fb:hp" opt; do
    case $opt in
        t) IMAGE_TAG="$OPTARG" ;;
        u) REGISTRY_USERNAME="$OPTARG" ;;
        f) BUILD_BACKEND=false ;;
        b) BUILD_FRONTEND=false ;;
        p) PUSH_TO_REGISTRY=true ;;
        h)
            echo "Usage: $0 [-t tag] [-u username] [-p] [-f] [-b]"
            echo "  -t: Image tag (default: latest)"
            echo "  -u: Registry username (e.g., Docker Hub username)"
            echo "  -p: Push images to registry after build"
            echo "  -f: Build frontend only"
            echo "  -b: Build backend only"
            echo "  -h: Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Build both services locally"
            echo "  $0 -t v1.0 -u myuser -p     # Build and push both with tag v1.0"
            echo "  $0 -f -t dev                # Build only frontend with tag dev"
            exit 0
            ;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
    esac
done

# Check if required files exist
echo "Checking project structure..."
MISSING_FILES=false

if [ "$BUILD_FRONTEND" = true ] && [ ! -f "$PROJECT_ROOT/$FRONTEND_DOCKERFILE" ]; then
    echo "Error: $FRONTEND_DOCKERFILE not found in project root"
    MISSING_FILES=true
fi

if [ "$BUILD_BACKEND" = true ] && [ ! -f "$PROJECT_ROOT/$BACKEND_DOCKERFILE" ]; then
    echo "Error: $BACKEND_DOCKERFILE not found in project root"
    MISSING_FILES=true
fi

if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "Error: requirements.txt not found in project root"
    MISSING_FILES=true
fi

if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
    echo "Warning: .env.production not found in project root"
fi

if [ "$MISSING_FILES" = true ]; then
    exit 1
fi

echo "✓ Project structure validated"
echo

# Docker login if pushing
if [ "$PUSH_TO_REGISTRY" = true ]; then
    if [ -z "$REGISTRY_USERNAME" ]; then
        echo "Error: Registry username required when pushing. Use -u flag."
        exit 1
    fi
    echo "Logging into Docker..."
    docker login
    if [ $? -ne 0 ]; then
        echo "Docker login failed. Exiting..."
        exit 1
    fi
    echo "✓ Docker login successful!"
    echo
fi

# Build Backend
if [ "$BUILD_BACKEND" = true ]; then
    echo "=========================================="
    echo "Building Backend Image"
    echo "=========================================="
    
    if [ -n "$REGISTRY_USERNAME" ]; then
        BACKEND_FULL_NAME="$REGISTRY_USERNAME/$BACKEND_NAME:$IMAGE_TAG"
    else
        BACKEND_FULL_NAME="$BACKEND_NAME:$IMAGE_TAG"
    fi
    
    echo "Image: $BACKEND_FULL_NAME"
    echo "Dockerfile: $BACKEND_DOCKERFILE"
    echo "Context: $PROJECT_ROOT"
    echo
    
    docker build -t "$BACKEND_FULL_NAME" -f "$PROJECT_ROOT/$BACKEND_DOCKERFILE" "$PROJECT_ROOT"
    
    if [ $? -ne 0 ]; then
        echo "❌ Backend build failed. Exiting..."
        exit 1
    fi
    
    echo "✓ Backend image built successfully: $BACKEND_FULL_NAME"
    echo
    
    # Push backend if enabled
    if [ "$PUSH_TO_REGISTRY" = true ]; then
        echo "Pushing backend image..."
        docker push "$BACKEND_FULL_NAME"
        if [ $? -ne 0 ]; then
            echo "❌ Backend push failed."
            exit 1
        fi
        echo "✓ Backend image pushed successfully"
        echo
    fi
fi

# Build Frontend
if [ "$BUILD_FRONTEND" = true ]; then
    echo "=========================================="
    echo "Building Frontend Image"
    echo "=========================================="
    
    if [ -n "$REGISTRY_USERNAME" ]; then
        FRONTEND_FULL_NAME="$REGISTRY_USERNAME/$FRONTEND_NAME:$IMAGE_TAG"
    else
        FRONTEND_FULL_NAME="$FRONTEND_NAME:$IMAGE_TAG"
    fi
    
    echo "Image: $FRONTEND_FULL_NAME"
    echo "Dockerfile: $FRONTEND_DOCKERFILE"
    echo "Context: $PROJECT_ROOT"
    echo
    
    docker build -t "$FRONTEND_FULL_NAME" -f "$PROJECT_ROOT/$FRONTEND_DOCKERFILE" "$PROJECT_ROOT"
    
    if [ $? -ne 0 ]; then
        echo "❌ Frontend build failed. Exiting..."
        exit 1
    fi
    
    echo "✓ Frontend image built successfully: $FRONTEND_FULL_NAME"
    echo
    
    # Push frontend if enabled
    if [ "$PUSH_TO_REGISTRY" = true ]; then
        echo "Pushing frontend image..."
        docker push "$FRONTEND_FULL_NAME"
        if [ $? -ne 0 ]; then
            echo "❌ Frontend push failed."
            exit 1
        fi
        echo "✓ Frontend image pushed successfully"
        echo
    fi
fi

echo "=========================================="
echo "✓ Build Complete!"
echo "=========================================="
echo
echo "Images built:"
if [ "$BUILD_BACKEND" = true ]; then
    echo "  Backend:  $BACKEND_FULL_NAME"
fi
if [ "$BUILD_FRONTEND" = true ]; then
    echo "  Frontend: $FRONTEND_FULL_NAME"
fi
echo
echo "To run with docker-compose, use:"
echo "  docker-compose up -d"
echo
echo "To run manually:"
if [ "$BUILD_BACKEND" = true ]; then
    echo "  docker run -d -p 8000:8000 --name backend $BACKEND_FULL_NAME"
fi
if [ "$BUILD_FRONTEND" = true ]; then
    echo "  docker run -d -p 8080:8080 --name frontend $FRONTEND_FULL_NAME"
fi
echo
echo "To view running containers:"
echo "  docker ps"
echo
echo "To view logs:"
if [ "$BUILD_BACKEND" = true ]; then
    echo "  docker logs backend"
fi
if [ "$BUILD_FRONTEND" = true ]; then
    echo "  docker logs frontend"
fi