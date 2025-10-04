#!/bin/bash

# Docker Hub Deploy Script
# This script logs in, builds with docker-compose, tags, and pushes images to Docker Hub

echo "=========================================="
echo "Docker Hub Deploy Script"
echo "=========================================="
echo

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.yml"
IMAGE_TAG="latest"

# Parse command line arguments
while getopts "t:f:h" opt; do
    case $opt in
        t) IMAGE_TAG="$OPTARG" ;;
        f) DOCKER_COMPOSE_FILE="$OPTARG" ;;
        h)
            echo "Usage: $0 [-t tag] [-f compose-file]"
            echo "  -t: Image tag (default: latest)"
            echo "  -f: Docker compose file (default: docker-compose.yml)"
            echo "  -h: Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 -t v1.0.0"
            echo "  $0 -t production -f docker-compose.prod.yml"
            exit 0
            ;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
    esac
done

# Check if docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: Docker compose file '$DOCKER_COMPOSE_FILE' not found"
    exit 1
fi

echo "Configuration:"
echo "  Image Tag: $IMAGE_TAG"
echo "  Compose File: $DOCKER_COMPOSE_FILE"
echo

# Step 1: Docker Login
echo "=========================================="
echo "Step 1: Docker Hub Login"
echo "=========================================="
echo

docker login

if [ $? -ne 0 ]; then
    echo "❌ Docker login failed. Exiting..."
    exit 1
fi

echo "✓ Docker login successful!"
echo

# Step 2: Retrieve Docker Hub Username
echo "=========================================="
echo "Step 2: Retrieving Docker Hub Username"
echo "=========================================="
echo

# Try multiple methods to get the username
REGISTRY_USERNAME=$(docker info 2>/dev/null | grep "Username" | awk '{print $2}')

# If that didn't work, try reading from docker config
if [ -z "$REGISTRY_USERNAME" ]; then
    if [ -f "$HOME/.docker/config.json" ]; then
        REGISTRY_USERNAME=$(cat "$HOME/.docker/config.json" | grep -o '"https://index.docker.io/v1/": *{[^}]*}' | grep -o '"username": *"[^"]*"' | cut -d'"' -f4)
    fi
fi

# If still empty, ask the user
if [ -z "$REGISTRY_USERNAME" ]; then
    echo "Could not automatically detect Docker Hub username."
    read -p "Please enter your Docker Hub username: " REGISTRY_USERNAME
    
    if [ -z "$REGISTRY_USERNAME" ]; then
        echo "❌ Docker Hub username is required. Exiting..."
        exit 1
    fi
fi

echo "✓ Using Docker Hub username: $REGISTRY_USERNAME"
echo

# Step 3: Build with Docker Compose
echo "=========================================="
echo "Step 3: Building with Docker Compose"
echo "=========================================="
echo

docker compose -f "$DOCKER_COMPOSE_FILE" up --build -d

if [ $? -ne 0 ]; then
    echo "❌ Docker compose build failed. Exiting..."
    exit 1
fi

echo "✓ Docker compose build and start successful!"
echo

# Step 4: List Docker Images
echo "=========================================="
echo "Step 4: Current Docker Images"
echo "=========================================="
echo

docker images

echo

# Step 5: Detect Image Names
echo "=========================================="
echo "Step 5: Detecting Built Images"
echo "=========================================="
echo

# Get all images and filter for backend and frontend
BACKEND_IMAGE=$(docker images --format "{{.Repository}}" | grep -i "backend" | head -n 1)
FRONTEND_IMAGE=$(docker images --format "{{.Repository}}" | grep -i "frontend" | head -n 1)

if [ -z "$BACKEND_IMAGE" ]; then
    echo "❌ Backend image not found. Looking for images with 'backend' in the name."
    echo "Available images:"
    docker images --format "{{.Repository}}"
    exit 1
fi

if [ -z "$FRONTEND_IMAGE" ]; then
    echo "❌ Frontend image not found. Looking for images with 'frontend' in the name."
    echo "Available images:"
    docker images --format "{{.Repository}}"
    exit 1
fi

echo "✓ Detected Images:"
echo "  Backend:  $BACKEND_IMAGE"
echo "  Frontend: $FRONTEND_IMAGE"
echo

# Step 6: Tag Images
echo "=========================================="
echo "Step 6: Tagging Images for Docker Hub"
echo "=========================================="
echo

# Get the full local image names with their current tags
BACKEND_LOCAL_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${BACKEND_IMAGE}:" | head -n 1)
FRONTEND_LOCAL_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${FRONTEND_IMAGE}:" | head -n 1)

# Extract just the image name (without any prefix)
BACKEND_NAME=$(basename "$BACKEND_IMAGE")
FRONTEND_NAME=$(basename "$FRONTEND_IMAGE")

# Define target image names
BACKEND_TARGET="${REGISTRY_USERNAME}/${BACKEND_NAME}:${IMAGE_TAG}"
FRONTEND_TARGET="${REGISTRY_USERNAME}/${FRONTEND_NAME}:${IMAGE_TAG}"

echo "Tagging Backend..."
echo "  Source: $BACKEND_LOCAL_IMAGE"
echo "  Target: $BACKEND_TARGET"

docker tag "$BACKEND_LOCAL_IMAGE" "$BACKEND_TARGET"

if [ $? -ne 0 ]; then
    echo "❌ Backend tagging failed. Exiting..."
    exit 1
fi
echo "✓ Backend tagged successfully"
echo

echo "Tagging Frontend..."
echo "  Source: $FRONTEND_LOCAL_IMAGE"
echo "  Target: $FRONTEND_TARGET"

docker tag "$FRONTEND_LOCAL_IMAGE" "$FRONTEND_TARGET"

if [ $? -ne 0 ]; then
    echo "❌ Frontend tagging failed. Exiting..."
    exit 1
fi
echo "✓ Frontend tagged successfully"
echo

# Step 7: Push Images to Docker Hub
echo "=========================================="
echo "Step 7: Pushing Images to Docker Hub"
echo "=========================================="
echo

echo "Pushing Backend Image..."
docker push "$BACKEND_TARGET"

if [ $? -ne 0 ]; then
    echo "❌ Backend push failed. Exiting..."
    exit 1
fi
echo "✓ Backend pushed successfully: $BACKEND_TARGET"
echo

echo "Pushing Frontend Image..."
docker push "$FRONTEND_TARGET"

if [ $? -ne 0 ]; then
    echo "❌ Frontend push failed. Exiting..."
    exit 1
fi
echo "✓ Frontend pushed successfully: $FRONTEND_TARGET"
echo

# Final Summary
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo
echo "Docker Hub Username: $REGISTRY_USERNAME"
echo
echo "Images pushed to Docker Hub:"
echo "  Backend:  $BACKEND_TARGET"
echo "  Frontend: $FRONTEND_TARGET"
echo
echo "View on Docker Hub:"
echo "  https://hub.docker.com/r/$REGISTRY_USERNAME/$BACKEND_NAME"
echo "  https://hub.docker.com/r/$REGISTRY_USERNAME/$FRONTEND_NAME"
echo
echo "To pull these images on another machine:"
echo "  docker pull $BACKEND_TARGET"
echo "  docker pull $FRONTEND_TARGET"
echo
echo "Current running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo