#!/bin/bash

# Docker cleanup script
# This script will login to Docker and perform a complete cleanup

echo "=========================================="
echo "Docker Cleanup Script"
echo "=========================================="
echo

# Docker login
echo "Logging into Docker..."
docker login
if [ $? -ne 0 ]; then
    echo "Docker login failed. Exiting..."
    exit 1
fi
echo "Docker login successful!"
echo

# Stop all running containers
echo "Stopping all running containers..."
docker ps -aq | xargs -r docker stop
echo "All containers stopped."
echo

# Remove all containers
echo "Removing all containers..."
docker ps -aq | xargs -r docker rm -f
echo "All containers removed."
echo

# Remove all images
echo "Removing all images..."
docker images -aq | xargs -r docker rmi -f
echo "All images removed."
echo

# Remove all volumes
echo "Removing all volumes..."
docker volume ls -q | xargs -r docker volume rm -f
echo "All volumes removed."
echo

# Prune builder cache
echo "Pruning builder cache..."
docker builder prune -af
echo "Builder cache pruned."
echo

echo "=========================================="
echo "Docker cleanup complete!"
echo "=========================================="