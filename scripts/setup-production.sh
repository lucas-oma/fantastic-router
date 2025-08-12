#!/bin/bash

# Fantastic Router - Production Setup Script
# This script helps set up Fantastic Router for production deployment

set -e  # Exit on any error

echo "🚀 Fantastic Router - Production Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Prerequisites check passed"

# Create production configuration
print_status "Setting up production configuration..."

# Create configs directory if it doesn't exist
mkdir -p configs

# Copy example config if it doesn't exist
if [ ! -f "configs/app.yaml" ]; then
    if [ -f "configs/app.example.yaml" ]; then
        cp configs/app.example.yaml configs/app.yaml
        print_success "Created configs/app.yaml from example"
    else
        print_error "configs/app.example.yaml not found"
        exit 1
    fi
else
    print_warning "configs/app.yaml already exists, skipping..."
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
# Fantastic Router - Production Environment Variables
# =================================================

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Database Configuration
DATABASE_URL=postgresql://fantastic_user:fantastic_pass@localhost:5432/fantastic_router
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# Cache Configuration
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this
API_KEY_1=your-api-key-1
API_KEY_2=your-api-key-2

# Application Configuration
CONFIG_FILE=/app/configs/app.yaml
APP_ENV=production
LOG_LEVEL=INFO
USE_FAST_PLANNER=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
EOF
    print_success "Created .env file"
    print_warning "Please edit .env file and add your actual API keys and secrets!"
else
    print_warning ".env file already exists, skipping..."
fi

# Create production Docker Compose file
print_status "Creating production Docker Compose file..."

cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: fantastic_router_app
    environment:
      - CONFIG_FILE=/app/configs/app.yaml
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./configs:/app/configs:ro
    networks:
      - fantastic_router_network

  postgres:
    image: postgres:15
    container_name: fantastic_router_postgres
    environment:
      POSTGRES_DB: fantastic_router
      POSTGRES_USER: fantastic_user
      POSTGRES_PASSWORD: fantastic_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fantastic_user -d fantastic_router"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - fantastic_router_network

  redis:
    image: redis:7-alpine
    container_name: fantastic_router_redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - fantastic_router_network

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: fantastic_router_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "8080:80"
    depends_on:
      - postgres
    restart: unless-stopped
    profiles:
      - admin
    networks:
      - fantastic_router_network

volumes:
  postgres_data:
  redis_data:

networks:
  fantastic_router_network:
    driver: bridge
EOF

print_success "Created docker-compose.prod.yml"

# Create production Makefile
print_status "Creating production Makefile..."

cat > Makefile.prod << EOF
# Fantastic Router - Production Makefile

.PHONY: help build up down logs clean backup restore

# Configuration
PORT ?= 8000
DB_PORT ?= 5432
REDIS_PORT ?= 6379
PGADMIN_PORT ?= 8080

help:
	@echo "🌟 Fantastic Router - Production Commands"
	@echo "========================================="
	@echo "📋 Configuration:"
	@echo "  PORT=$(PORT) (API server)"
	@echo "  DB_PORT=$(DB_PORT) (PostgreSQL)"
	@echo "  REDIS_PORT=$(REDIS_PORT) (Redis)"
	@echo "  PGADMIN_PORT=$(PGADMIN_PORT) (pgAdmin)"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  build      - Build production Docker image"
	@echo "  up         - Start all production services"
	@echo "  down       - Stop all services"
	@echo "  logs       - View application logs"
	@echo "  logs-db    - View database logs"
	@echo ""
	@echo "🔧 Management Commands:"
	@echo "  backup     - Backup database"
	@echo "  restore    - Restore database from backup"
	@echo "  clean      - Clean up containers and volumes"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  health     - Check service health"
	@echo "  stats      - View service statistics"

build:
	@echo "🔨 Building production Docker image..."
	docker-compose -f docker-compose.prod.yml build

up:
	@echo "🚀 Starting production services..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Services started!"
	@echo "📊 API Server: http://localhost:$(PORT)"
	@echo "🗄️  Database: localhost:$(DB_PORT)"
	@echo "🔴 Redis: localhost:$(REDIS_PORT)"
	@echo "🔍 pgAdmin: http://localhost:$(PGADMIN_PORT) (admin / admin)"

down:
	@echo "🛑 Stopping all services..."
	docker-compose -f docker-compose.prod.yml down

logs:
	@echo "📋 Application logs:"
	docker-compose -f docker-compose.prod.yml logs -f app

logs-db:
	@echo "📋 Database logs:"
	docker-compose -f docker-compose.prod.yml logs -f postgres

health:
	@echo "🏥 Checking service health..."
	@echo "📊 API Health:"
	curl -s http://localhost:$(PORT)/api/v1/health | python3 -m json.tool || echo "API not responding"
	@echo ""
	@echo "🗄️  Database Health:"
	docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U fantastic_user -d fantastic_router || echo "Database not responding"
	@echo ""
	@echo "🔴 Redis Health:"
	docker-compose -f docker-compose.prod.yml exec redis redis-cli ping || echo "Redis not responding"

stats:
	@echo "📊 Service Statistics:"
	@echo "🐳 Container Status:"
	docker-compose -f docker-compose.prod.yml ps
	@echo ""
	@echo "💾 Resource Usage:"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

backup:
	@echo "💾 Creating database backup..."
	mkdir -p backups
	docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U fantastic_user fantastic_router > backups/fantastic_router_\$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

restore:
	@echo "📥 Restoring database from backup..."
	@if [ -z "\$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify backup file: make restore BACKUP_FILE=backups/filename.sql"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec -T postgres psql -U fantastic_user -d fantastic_router < \$(BACKUP_FILE)
	@echo "✅ Database restored from \$(BACKUP_FILE)"

clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Development helpers
dev-up:
	@echo "🛠️  Starting development environment..."
	docker-compose -f docker/docker-compose.yml up -d

dev-down:
	@echo "🛠️  Stopping development environment..."
	docker-compose -f docker/docker-compose.yml down
EOF

print_success "Created Makefile.prod"

# Create systemd service file (optional)
print_status "Creating systemd service file..."

cat > fantastic-router.service << EOF
[Unit]
Description=Fantastic Router API Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

print_success "Created fantastic-router.service"
print_warning "To install as systemd service: sudo cp fantastic-router.service /etc/systemd/system/ && sudo systemctl enable fantastic-router"

# Create monitoring script
print_status "Creating monitoring script..."

cat > scripts/monitor.sh << 'EOF'
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
EOF

chmod +x scripts/monitor.sh
print_success "Created scripts/monitor.sh"

# Create backup script
print_status "Creating backup script..."

cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# Fantastic Router - Backup Script

set -e

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fantastic_router_$DATE.sql"

echo "💾 Creating backup: $BACKUP_FILE"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U fantastic_user fantastic_router > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE.gz"

# Keep only last 7 backups
find $BACKUP_DIR -name "fantastic_router_*.sql.gz" -mtime +7 -delete

echo "🧹 Cleaned up backups older than 7 days"
EOF

chmod +x scripts/backup.sh
print_success "Created scripts/backup.sh"

# Final instructions
echo ""
echo "🎉 Production setup complete!"
echo "============================="
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - OPENAI_API_KEY"
echo "   - DATABASE_URL (if using external database)"
echo "   - JWT_SECRET (change the default)"
echo ""
echo "2. Customize configs/app.yaml for your domain:"
echo "   - Update site.domain and site.base_url"
echo "   - Define your entities and route patterns"
echo ""
echo "3. Start the services:"
echo "   make -f Makefile.prod up"
echo ""
echo "4. Monitor the services:"
echo "   ./scripts/monitor.sh"
echo ""
echo "5. Set up automated backups:"
echo "   crontab -e"
echo "   # Add: 0 2 * * * $(pwd)/scripts/backup.sh"
echo ""
echo "📚 Documentation:"
echo "   - Production guide: docs/deployment.md"
echo "   - API docs: http://localhost:8000/docs (after starting)"
echo ""
print_success "Setup complete! 🚀" 