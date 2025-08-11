# Quick Start Guide

Get Fantastic Router running in **5 minutes** with this step-by-step guide.

## 🚀 Prerequisites

- **Docker** & **Docker Compose** installed
- **Python 3.9+** (for local development)
- **An LLM API key** (OpenAI, Google AI, or Anthropic) OR **Ollama** for local LLMs

## 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/fantastic-router
cd fantastic-router
```

### 2. Quick Setup

```bash
# One command setup!
make setup
```

This will:
- ✅ Create a comprehensive `.env` file in `docker/`
- ✅ Build the Docker image
- ✅ Start the database
- ✅ Show you next steps

### 3. Configure Your LLM Provider

Edit `docker/.env` and choose **ONE** of these options:

#### Option A: OpenAI (Most Popular)
```bash
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-3.5-turbo-1106
```

#### Option B: Google Gemini (Fastest & Cheapest)
```bash
# Get API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-google-ai-key-here
GEMINI_MODEL=gemini-1.5-flash
```

#### Option C: Anthropic Claude
```bash
# Get API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

#### Option D: Local LLM (Ollama)
```bash
# Install Ollama first
brew install ollama  # macOS
# OR: curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# Pull a model
ollama pull llama3.1:8b

# Configure
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### 4. Start Everything

```bash
make up
```

This starts:
- 🌐 **FastAPI Server**: http://localhost:8000
- 🗄️ **PostgreSQL**: localhost:5432  
- 🔍 **pgAdmin**: http://localhost:8080 (optional)

### 5. Test It!

```bash
# Quick test
make test-server

# OR test manually
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "show me James Smith monthly income"}'
```

## 🎯 Your First Request

### Example Query

```bash
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{
    "query": "show me James Smith monthly income",
    "user_role": "admin"
  }'
```

### Expected Response

```json
{
  "success": true,
  "action_plan": {
    "action_type": "NAVIGATE",
    "route": "/landlords/james-smith-123/financials",
    "confidence": 0.87,
    "reasoning": "User wants to navigate to James Smith's financial information..."
  },
  "performance": {
    "duration_ms": 1250,
    "level": "good"
  }
}
```

## 🌐 Explore the API

### Interactive Documentation

Visit **http://localhost:8000/docs** to:
- 📋 See all available endpoints
- 🧪 Test requests directly in your browser
- 📖 View detailed schemas and examples
- 📥 Download the OpenAPI specification

### Key Endpoints

- **POST `/api/v1/plan`** - Main routing endpoint
- **GET `/api/v1/health`** - System health check
- **GET `/`** - Basic information
- **GET `/docs`** - Interactive API documentation

## 🧪 Try Different Queries

The system comes with sample data for a **property management** domain:

### Navigation Queries
```bash
# Find specific people
curl -X POST http://localhost:8000/api/v1/plan \
  -d '{"query": "show me James Smith monthly income"}'

curl -X POST http://localhost:8000/api/v1/plan \
  -d '{"query": "edit John Doe contact information"}'
```

### Creation Queries
```bash
# Create new resources
curl -X POST http://localhost:8000/api/v1/plan \
  -d '{"query": "create new property"}'

curl -X POST http://localhost:8000/api/v1/plan \
  -d '{"query": "add new tenant"}'
```

### Search Queries
```bash
# Find and filter data
curl -X POST http://localhost:8000/api/v1/plan \
  -d '{"query": "list all tenants"}'

curl -X POST http://localhost:8000/api/v1/plan \
  -d '{"query": "search for properties in downtown"}'
```

## 🎭 Understanding the Response

Every response includes:

### Action Plan
- **`route`**: The URL path to navigate to
- **`action_type`**: What kind of action (NAVIGATE, CREATE, EDIT, etc.)
- **`confidence`**: How confident the AI is (0-1)
- **`reasoning`**: Why this route was chosen

### Entities
- **Resolved people/objects** from your database
- **Confidence scores** for each match
- **Full metadata** from the database

### Performance
- **`duration_ms`**: How long it took
- **`level`**: Performance rating (🚀 excellent, 🏃 good, 🐌 slow, etc.)

## ⚡ Performance Tuning

### Check Your Performance

The system includes performance indicators:
- **🚀 < 1000ms**: Excellent (single optimized LLM call)
- **🏃 1000-3000ms**: Good  
- **🐌 3000-5000ms**: Needs optimization
- **💩 5000-10000ms**: Slow
- **💀 > 10000ms**: Critical issues

### Optimization Tips

1. **Use Gemini** for fastest responses
2. **Use local models** (Ollama) for privacy and no API costs
3. **Enable fast planner** (default: enabled)
4. **Check your internet connection** for cloud LLMs

## 🏗️ Database Exploration

### View Sample Data

```bash
# Connect to database
make shell-db

# View sample users
SELECT name, email, role FROM users LIMIT 10;

# View properties
SELECT name, address, status FROM properties LIMIT 5;
```

### Use pgAdmin (Optional)

Visit **http://localhost:8080**:
- 📧 **Email**: admin@fantastic-router.com
- 🔑 **Password**: admin

## 🎛️ Configuration

### Environment Variables

Key settings in `docker/.env`:

```bash
# Performance
USE_FAST_PLANNER=true        # Use optimized single-call planner
LLM_TIMEOUT=60               # LLM request timeout
LLM_TEMPERATURE=0.1          # Response creativity (0=deterministic)

# Database
DATABASE_URL=postgresql://...
DB_MAX_CONNECTIONS=10
DB_TIMEOUT=30

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

### Custom Domain Configuration

The system comes configured for **property management**. To adapt it for your domain:

1. **Edit** `examples/quickstart/routes.json`
2. **Update** entity definitions
3. **Modify** route patterns
4. **Restart** the system

See [Configuration Guide](configuration.md) for details.

## 🚨 Troubleshooting

### Common Issues

**"LLM timeout"**:
```bash
# Check your API key
curl http://localhost:8000/api/v1/health

# Try a different model
OPENAI_MODEL=gpt-3.5-turbo  # Faster than GPT-4
```

**"Database connection failed"**:
```bash
# Restart database
make restart-db

# Check database status
make test-db
```

**"Planning failed"**:
```bash
# Check logs
docker-compose -f docker/docker-compose.yml --env-file .env logs app

# Try a simpler query
curl -d '{"query": "help"}' http://localhost:8000/api/v1/plan
```

### Get Help

- 📋 **Check the logs**: `make logs`
- 🔍 **Test database**: `make test-db`
- 🌐 **Test server**: `make test-server`
- 💬 **GitHub Issues**: Report problems
- 📖 **Full docs**: See [Documentation Index](index.md)

## 🎉 Next Steps

Now that you have it running:

1. **📖 Read the [Architecture Guide](architecture.md)** to understand how it works
2. **🔧 Try the [Configuration Guide](configuration.md)** to adapt it to your domain
3. **🌐 Explore the [API Reference](api.md)** for detailed endpoint documentation
4. **⚡ Check out [Performance Optimization](advanced/performance.md)** tips

## 🛟 Quick Commands Reference

```bash
# Setup & Start
make setup           # Initial setup
make up             # Start all services
make down           # Stop all services
make restart        # Restart everything

# Testing
make test-server    # Test API endpoints
make test-db        # Test database
make test-all-llms  # Compare LLM providers

# Development
make logs           # View logs
make shell          # Enter app container
make shell-db       # Connect to database
make build          # Rebuild Docker image

# Cleanup
make clean          # Stop and remove containers
make clean-all      # Remove everything including images
```

**Ready to dive deeper?** → [Architecture Overview](architecture.md)

---

**🎯 Stuck?** Open a [GitHub Issue](https://github.com/yourusername/fantastic-router/issues) - we're here to help! 