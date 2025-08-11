#!/bin/bash

# Fantastic Router - Monitoring Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PORT=${PORT:-8000}
DB_PORT=${DB_PORT:-5432}
REDIS_PORT=${REDIS_PORT:-6379}

echo "🔍 Fantastic Router - Health Check"
echo "=================================="

# Check API health
print_status "Checking API health..."
if curl -s http://localhost:$PORT/api/v1/health > /dev/null; then
    print_success "API is healthy"
else
    print_error "API is not responding"
fi

# Check database
print_status "Checking database..."
if docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U fantastic_user -d fantastic_router > /dev/null 2>&1; then
    print_success "Database is healthy"
else
    print_error "Database is not responding"
fi

# Check Redis
print_status "Checking Redis..."
if docker-compose -f docker-compose.prod.yml exec redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is healthy"
else
    print_error "Redis is not responding"
fi

# Check container status
print_status "Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
