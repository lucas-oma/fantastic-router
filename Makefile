# Fantastic Router - Development Makefile

.PHONY: help build up down test test-db test-real clean logs shell

# Default target
help:
	@echo "🌟 Fantastic Router - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  build      - Build the Docker image"
	@echo "  up         - Start all services (app + database)"
	@echo "  up-db      - Start only the database"
	@echo "  down       - Stop all services"
	@echo "  logs       - View application logs"
	@echo "  logs-db    - View database logs"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  test         - Run basic test with mock data"
	@echo "  test-real    - Run test with real database and LLM"
	@echo "  test-gemini  - Compare Gemini vs OpenAI performance"
	@echo "  test-all-llms- Test all available LLM providers"
	@echo "  test-db      - Test database connection"
	@echo "  test-server  - Test the FastAPI server endpoints"
	@echo ""
	@echo "🔧 Development Commands:"
	@echo "  shell      - Open shell in app container"
	@echo "  db-shell   - Open PostgreSQL shell"
	@echo "  clean      - Clean up containers and volumes"
	@echo ""
	@echo "📋 Prerequisites:"
	@echo "  - Docker and Docker Compose installed"
	@echo "  - Copy docker/.env.example to docker/.env and add your OpenAI API key"

# Docker commands
build:
	@echo "🔨 Building Fantastic Router Docker image..."
	docker-compose -f docker/docker-compose.yml build

up:
	@echo "🚀 Starting Fantastic Router (app + database)..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "✅ Services started!"
	@echo "📊 Database: localhost:5432"
	@echo "🔍 pgAdmin: http://localhost:8080 (admin@fantastic-router.com / admin)"

up-db:
	@echo "🗄️  Starting database only..."
	docker-compose -f docker/docker-compose.yml up -d postgres
	@echo "✅ Database started on localhost:5432"

down:
	@echo "🛑 Stopping all services..."
	docker-compose -f docker/docker-compose.yml down

logs:
	@echo "📋 Application logs:"
	docker-compose -f docker/docker-compose.yml logs -f app

logs-db:
	@echo "📋 Database logs:"
	docker-compose -f docker/docker-compose.yml logs -f postgres

# Testing commands
test:
	@echo "🧪 Running basic test with mock data..."
	docker-compose -f docker/docker-compose.yml run --rm app python examples/quickstart/example.py

test-real: up-db
	@echo "🧪 Running test with real database..."
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	docker-compose -f docker/docker-compose.yml run --rm app python examples/quickstart/test_with_real_db.py

test-gemini: up-db
	@echo "🧪 Testing with Gemini vs OpenAI..."
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	docker-compose -f docker/docker-compose.yml run --rm app python examples/quickstart/test_gemini.py compare

test-all-llms: up-db
	@echo "🧪 Testing all available LLM providers..."
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	docker-compose -f docker/docker-compose.yml run --rm app python examples/quickstart/test_all_llms.py

test-db:
	@echo "🔍 Testing database connection..."
	docker-compose -f docker/docker-compose.yml exec postgres pg_isready -U fantastic_user -d property_mgmt
	@echo "📊 Sample data:"
	docker-compose -f docker/docker-compose.yml exec postgres psql -U fantastic_user -d property_mgmt -c "SELECT name, email, role FROM users LIMIT 5;"

test-server: up
	@echo "🌐 Testing FastAPI server endpoints..."
	@echo "⏳ Waiting for server to be ready..."
	@sleep 10
	@echo "📊 Health check:"
	curl -s http://localhost:8000/api/v1/health | python3 -m json.tool || echo "Health check failed"
	@echo ""
	@echo "📍 API Documentation available at: http://localhost:8000/docs"
	@echo "🔍 Testing plan endpoint:"
	curl -s -X POST http://localhost:8000/api/v1/plan \
		-H "Content-Type: application/json" \
		-d '{"query": "show me James Smith monthly income"}' | python3 -m json.tool || echo "Plan endpoint failed"

test-caching: up
	@echo "🧪 Testing dual caching system..."
	@echo "⏳ Waiting for server to be ready..."
	@sleep 10
	@echo "🚀 Running caching tests..."
	python3 examples/quickstart/test_caching.py

test-natural-queries: up
	@echo "🧪 Testing natural query variations..."
	@echo "⏳ Waiting for server to be ready..."
	@sleep 10
	@echo "🚀 Running natural query tests..."
	python3 examples/quickstart/test_natural_queries.py

test-route-validation: up
	@echo "🧪 Testing route validation..."
	@echo "⏳ Waiting for server to be ready..."
	@sleep 10
	@echo "🚀 Running route validation tests..."
	python3 examples/quickstart/test_route_validation.py

# Development commands
shell:
	@echo "🐚 Opening shell in app container..."
	docker-compose -f docker/docker-compose.yml run --rm app /bin/bash

db-shell:
	@echo "🗄️  Opening PostgreSQL shell..."
	docker-compose -f docker/docker-compose.yml exec postgres psql -U fantastic_user -d property_mgmt

clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Setup commands
setup:
	@echo "🔧 Setting up development environment..."
	@if [ ! -f docker/.env ]; then \
		echo "📝 Creating comprehensive .env file..."; \
		echo "# Environment variables for Fantastic Router" > docker/.env; \
		echo "" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "# LLM API Keys (choose one or more)" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# OpenAI (GPT models)" >> docker/.env; \
		echo "OPENAI_API_KEY=your-openai-api-key-here" >> docker/.env; \
		echo "OPENAI_MODEL=gpt-3.5-turbo-1106" >> docker/.env; \
		echo "OPENAI_MAX_TOKENS=1000" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# Google Gemini (fastest and often cheapest cloud option)" >> docker/.env; \
		echo "GEMINI_API_KEY=your-google-ai-api-key-here" >> docker/.env; \
		echo "GOOGLE_AI_API_KEY=your-google-ai-api-key-here" >> docker/.env; \
		echo "GEMINI_MODEL=gemini-1.5-flash" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# Anthropic Claude (if you have direct API access)" >> docker/.env; \
		echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here" >> docker/.env; \
		echo "ANTHROPIC_MODEL=claude-3-haiku-20240307" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "# Local LLM Configuration (Ollama)" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# Ollama server URL (default: http://localhost:11434)" >> docker/.env; \
		echo "OLLAMA_BASE_URL=http://localhost:11434" >> docker/.env; \
		echo "# Recommended: mistral-small3.2:24b, llama3.1:8b, llama3.1:1b" >> docker/.env; \
		echo "OLLAMA_MODEL=llama3.1:8b" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "# Database Configuration" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "DATABASE_URL=postgresql://fantastic_user:fantastic_pass@postgres:5432/property_mgmt" >> docker/.env; \
		echo "DB_MAX_CONNECTIONS=10" >> docker/.env; \
		echo "DB_TIMEOUT=30" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "# Application Configuration" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "APP_ENV=development" >> docker/.env; \
		echo "LOG_LEVEL=INFO" >> docker/.env; \
		echo "USE_FAST_PLANNER=true" >> docker/.env; \
		echo "LLM_TIMEOUT=60" >> docker/.env; \
		echo "LLM_TEMPERATURE=0.1" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "# Setup Instructions" >> docker/.env; \
		echo "# =============================================================================" >> docker/.env; \
		echo "# 1. Choose your LLM provider:" >> docker/.env; \
		echo "#    - Cloud: Set OPENAI_API_KEY or GEMINI_API_KEY" >> docker/.env; \
		echo "#    - Local: Install Ollama and set OLLAMA_MODEL" >> docker/.env; \
		echo "# 2. Test: make test-real or make test-all-llms" >> docker/.env; \
		echo "" >> docker/.env; \
		echo "⚠️  Please edit docker/.env and add your API keys!"; \
		echo "💡 For local LLMs: brew install ollama && ollama pull llama3.1:8b"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@echo "🔨 Building Docker image..."
	$(MAKE) build
	@echo "🗄️  Starting database..."
	$(MAKE) up-db
	@echo ""
	@echo "🎉 Setup complete! Next steps:"
	@echo "1. Edit docker/.env and add your LLM provider keys:"
	@echo "   - Cloud: OPENAI_API_KEY or GEMINI_API_KEY"
	@echo "   - Local: Install Ollama (brew install ollama)"
	@echo "2. Test your setup:"
	@echo "   - make test-real (single provider)"
	@echo "   - make test-all-llms (compare all providers)"
	@echo "3. Run 'make up' to start all services"

# Quick start for new users
quickstart: setup
	@echo ""
	@echo "🚀 Running quickstart test..."
	@sleep 5
	$(MAKE) test

# Install local development dependencies
dev-install:
	@echo "📦 Installing local development dependencies..."
	pip install -e "packages/fantastic_router_core[dev,openai,postgres]"
	pip install python-dotenv
	@echo "✅ Development dependencies installed!"
