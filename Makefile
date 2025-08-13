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
	@echo "  test-system-db - Test system database connection"
	@echo "  test-server  - Test the FastAPI server endpoints"
	@echo ""
	@echo "🔑 API Key Management:"
	@echo "  generate-api-key - Generate a new API key for testing"
	@echo ""
	@echo "🔧 Development Commands:"
	@echo "  shell      - Open shell in app container"
	@echo "  db-shell   - Open PostgreSQL shell"
	@echo "  clean      - Clean up containers and volumes"
	@echo ""
	@echo "📋 Prerequisites:"
	@echo "  - Docker and Docker Compose installed"
	@echo "  - Copy .env.example to .env and add your API keys"

# Docker commands
build:
	@echo "🔨 Building Fantastic Router Docker image..."
	docker-compose -f docker/docker-compose.yml --env-file .env build

up:
	@echo "🚀 Starting Fantastic Router (app + databases)..."
	docker-compose -f docker/docker-compose.yml --env-file .env up -d
	@echo "✅ Services started!"
	@echo "📊 Domain Database: localhost:5432"
	@echo "🔧 System Database: localhost:5433"

up-db:
	@echo "🗄️  Starting databases only..."
	docker-compose -f docker/docker-compose.yml --env-file .env up -d postgres system_db
	@echo "✅ Domain Database started on localhost:5432"
	@echo "✅ System Database started on localhost:5433"

up-admin:
	@echo "🗄️  Starting databases and pgAdmin..."
	docker-compose -f docker/docker-compose.yml --env-file .env --profile admin up -d
	@echo "✅ Domain Database started on localhost:5432"
	@echo "✅ System Database started on localhost:5433"
	@echo "🔍 pgAdmin: http://localhost:$$(grep PGADMIN_PORT .env | cut -d'=' -f2 || echo 8080) ($$(grep PGADMIN_EMAIL .env | cut -d'=' -f2 || echo admin@pgadmin.com) / $$(grep PGADMIN_PASSWORD .env | cut -d'=' -f2 || echo admin))"

down:
	@echo "🛑 Stopping all services..."
	docker-compose -f docker/docker-compose.yml --env-file .env down --remove-orphans

logs:
	@echo "📋 Application logs:"
	docker-compose -f docker/docker-compose.yml --env-file .env logs -f app

logs-db:
	@echo "📋 Domain Database logs:"
	docker-compose -f docker/docker-compose.yml --env-file .env logs -f postgres
	@echo "📋 System Database logs:"
	docker-compose -f docker/docker-compose.yml --env-file .env logs -f system_db

# Testing commands
test:
	@echo "🧪 Running basic test with mock data..."
	docker-compose -f docker/docker-compose.yml --env-file .env run --rm app python examples/quickstart/example.py

test-real: up-db
	@echo "🧪 Running test with real database..."
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	docker-compose -f docker/docker-compose.yml --env-file .env run --rm app python examples/quickstart/test_with_real_db.py

test-gemini: up-db
	@echo "🧪 Testing with Gemini vs OpenAI..."
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	docker-compose -f docker/docker-compose.yml --env-file .env run --rm app python examples/quickstart/test_gemini.py compare

test-all-llms: up-db
	@echo "🧪 Testing all available LLM providers..."
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	docker-compose -f docker/docker-compose.yml --env-file .env run --rm app python examples/quickstart/test_all_llms.py

test-db:
	@echo "🔍 Testing domain database connection..."
	docker-compose -f docker/docker-compose.yml --env-file .env exec postgres pg_isready -U fantastic_user -d property_mgmt
	@echo "📊 Sample data:"
	docker-compose -f docker/docker-compose.yml --env-file .env exec postgres psql -U fantastic_user -d property_mgmt -c "SELECT name, email, role FROM users LIMIT 5;"

test-system-db:
	@echo "🔍 Testing system database connection..."
	docker-compose -f docker/docker-compose.yml --env-file .env exec system_db pg_isready -U system_user -d fantastic_router_system
	@echo "📊 System data:"
	docker-compose -f docker/docker-compose.yml --env-file .env exec system_db psql -U system_user -d fantastic_router_system -c "SELECT username, email, role FROM users;"
	@echo "🔑 API Keys:"
	docker-compose -f docker/docker-compose.yml --env-file .env exec system_db psql -U system_user -d fantastic_router_system -c "SELECT key_name, is_active FROM api_keys;"
	@echo "🤖 LLM Providers:"
	docker-compose -f docker/docker-compose.yml --env-file .env exec system_db psql -U system_user -d fantastic_router_system -c "SELECT provider_name, model_name, is_default FROM llm_providers;"

generate-api-key:
	@echo "🔑 Generating new API key..."
	docker-compose -f docker/docker-compose.yml --env-file .env run --rm app python examples/quickstart/generate_api_key.py

test-server: up
	@echo "🌐 Testing FastAPI server endpoints..."
	@echo "⏳ Waiting for server to be ready..."
	@sleep 10
	@echo "📊 Health check:"
	curl -s http://localhost:8000/api/v1/health | python3 -m json.tool || echo "Health check failed"
	@echo ""
	@echo "📍 API Documentation available at: http://localhost:8000/docs"
	@echo "🔍 Testing plan endpoint:"
	@if [ -z "$$FR_API_KEY" ]; then \
		echo "⚠️  No FR_API_KEY set. Set it with: export FR_API_KEY=your_api_key_here"; \
		echo "   Or run: make generate-api-key to get a key"; \
	fi
	curl -s -X POST http://localhost:8000/api/v1/plan \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $${FR_API_KEY:-}" \
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
	docker-compose -f docker/docker-compose.yml --env-file .env run --rm app /bin/bash

db-shell:
	@echo "🗄️  Opening PostgreSQL shell..."
	docker-compose -f docker/docker-compose.yml --env-file .env exec postgres psql -U fantastic_user -d property_mgmt

clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose -f docker/docker-compose.yml --env-file .env down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Setup commands
setup:
	@echo "🔧 Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating comprehensive .env file..."; \
		echo "# Environment variables for Fantastic Router" > .env; \
		echo "" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# LLM API Keys (choose one or more)" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "" >> .env; \
		echo "# OpenAI (GPT models)" >> .env; \
		echo "OPENAI_API_KEY=your-openai-api-key-here" >> .env; \
		echo "OPENAI_MODEL=gpt-3.5-turbo-1106" >> .env; \
		echo "LLM_MAX_TOKENS=1000" >> .env; \
		echo "" >> .env; \
		echo "# Google Gemini (fastest and often cheapest cloud option)" >> .env; \
		echo "GEMINI_API_KEY=your-google-ai-api-key-here" >> .env; \
		echo "GOOGLE_AI_API_KEY=your-google-ai-api-key-here" >> .env; \
		echo "GEMINI_MODEL=gemini-1.5-flash" >> .env; \
		echo "" >> .env; \
		echo "# Anthropic Claude (if you have direct API access)" >> .env; \
		echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here" >> .env; \
		echo "ANTHROPIC_MODEL=claude-3-haiku-20240307" >> .env; \
		echo "" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# Local LLM Configuration (Ollama)" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "" >> .env; \
		echo "# Ollama server URL (default: http://localhost:11434)" >> .env; \
		echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env; \
		echo "# Recommended: mistral-small3.2:24b, llama3.1:8b, llama3.1:1b" >> .env; \
		echo "OLLAMA_MODEL=llama3.1:8b" >> .env; \
		echo "" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# Database Configuration" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "" >> .env; \
		echo "DATABASE_URL=postgresql://fantastic_user:fantastic_pass@postgres:5432/property_mgmt" >> .env; \
		echo "DB_MAX_CONNECTIONS=10" >> .env; \
		echo "DB_TIMEOUT=30" >> .env; \
		echo "" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# pgAdmin Configuration" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "" >> .env; \
		echo "# pgAdmin port (change if 8080 is already in use)" >> .env; \
		echo "PGADMIN_PORT=8080" >> .env; \
		echo "# pgAdmin credentials (change for production)" >> .env; \
		echo "PGADMIN_EMAIL=admin@pgadmin.com" >> .env; \
		echo "PGADMIN_PASSWORD=admin" >> .env; \
		echo "" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# Application Configuration" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "" >> .env; \
		echo "APP_ENV=development" >> .env; \
		echo "LOG_LEVEL=INFO" >> .env; \
		echo "USE_FAST_PLANNER=true" >> .env; \
		echo "LLM_TIMEOUT=60" >> .env; \
		echo "LLM_TEMPERATURE=0.1" >> .env; \
		echo "" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# Setup Instructions" >> .env; \
		echo "# =============================================================================" >> .env; \
		echo "# 1. Choose your LLM provider:" >> .env; \
		echo "#    - Cloud: Set OPENAI_API_KEY or GEMINI_API_KEY" >> .env; \
		echo "#    - Local: Install Ollama and set OLLAMA_MODEL" >> .env; \
		echo "# 2. Test: make test-real or make test-all-llms" >> .env; \
		echo "" >> .env; \
		echo "⚠️  Please edit .env and add your API keys!"; \
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
	@echo "1. Edit .env and add your LLM provider keys:"
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
