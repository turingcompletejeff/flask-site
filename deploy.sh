#!/bin/bash

# Docker Deployment Script for Flask Site
# This replaces your manual SSH + screen deployment process

set -e  # Exit on any error

# Configuration
IMAGE_NAME="flask-site"
TAG="latest"
CONTAINER_NAME="flask-site-prod"

echo "🚀 Starting Docker deployment for Flask Site..."

# Pull latest code
echo "📦 Pulling latest changes..."
git pull origin main

# Build new Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME:$TAG .

# Stop and remove existing container if it exists
echo "🛑 Stopping existing container (if running)..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Start new container
echo "▶️  Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  $IMAGE_NAME:$TAG

# Wait for container to be healthy
echo "🔍 Waiting for container to be healthy..."
sleep 10

# Check if container is running
if docker ps --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
    echo "✅ Deployment successful! Container is running."
    docker logs --tail 20 $CONTAINER_NAME
else
    echo "❌ Deployment failed! Container is not running."
    docker logs $CONTAINER_NAME
    exit 1
fi

# Clean up old images (keep latest 3)
echo "🧹 Cleaning up old images..."
docker images $IMAGE_NAME --format "table {{.ID}}" | tail -n +4 | xargs -r docker rmi 2>/dev/null || true

echo "🎉 Deployment complete!"
echo "📊 Container status:"
docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"