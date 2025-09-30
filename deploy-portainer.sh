#!/bin/bash

# Portainer deployment script for flask-site
# Usage: ./deploy-portainer.sh

set -e  # Exit on any error

echo "🚀 Starting Portainer deployment..."

# Navigate to project directory
cd /home/shades/git/flask-site

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Build new image
echo "🔨 Building new Docker image..."
docker build -t flask-site:latest .

# Get current running containers
echo "🔍 Checking current containers..."
FLASK_CONTAINER=$(docker ps --filter "name=flask-site-prod" --format "{{.ID}}" || echo "")
POSTGRES_CONTAINER=$(docker ps --filter "name=flask-postgres-prod" --format "{{.ID}}" || echo "")

if [ ! -z "$FLASK_CONTAINER" ]; then
    echo "🔄 Restarting Flask container with new image..."
    docker stop $FLASK_CONTAINER
    docker rm $FLASK_CONTAINER
    echo "✅ Old Flask container removed"
else
    echo "⚠️  No running Flask container found"
fi

echo "🎯 New image ready: flask-site:latest"
echo "📋 Next steps:"
echo "  1. Go to Portainer web interface"
echo "  2. Stop the flask-site stack"
echo "  3. Start the flask-site stack"
echo "  4. Verify deployment at http://your-server:8000"

# Optional: Show image info
echo ""
echo "📊 Current flask-site images:"
docker images | grep flask-site
