#!/bin/bash

# Docker Compose Deployment Script for Flask Site
# Uses Docker Compose to manage both Flask app and PostgreSQL database

set -e  # Exit on any error

# Configuration
COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="flask-site"

echo "🚀 Starting Docker Compose deployment for Flask Site..."

# Pull latest code
echo "📦 Pulling latest changes..."
git pull origin main

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down

# Build and start all services
echo "🔨 Building and starting services..."
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up --build -d

# Wait for services to be healthy
echo "🔍 Waiting for services to start..."
sleep 15

# Check if containers are running
echo "📊 Checking container status..."
if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME ps | grep -q "Up"; then
    echo "✅ Deployment successful! Services are running."
    echo ""
    echo "📊 Container status:"
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME ps
    echo ""
    echo "📋 Recent logs:"
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs --tail 10
else
    echo "❌ Deployment failed! Some services are not running."
    echo ""
    echo "📋 Error logs:"
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs
    exit 1
fi

# Clean up old images (keep latest 3)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"
echo "🌐 Application should be accessible on configured ports"
echo ""
echo "💡 Useful commands:"
echo "  View logs:    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f"
echo "  Stop services: docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down"
echo "  Restart:      docker compose -f $COMPOSE_FILE -p $PROJECT_NAME restart"
