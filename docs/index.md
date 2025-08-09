# Fantastic Router Documentation

<div align="center">
  <img src="../assets/images/docs/fantastic-router.png" alt="Fantastic Router" height="120" />
</div>

Welcome to **Fantastic Router** - the LLM-powered intent routing system that transforms natural language queries into precise navigation actions for web applications.

## 🚀 Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/fantastic-router
cd fantastic-router
make setup

# 2. Add your API keys to docker/.env
# 3. Start everything
make up

# 4. Test it
make test-server
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to explore the interactive API.

## 📚 Documentation

### Getting Started
- [**Quick Start Guide**](quickstart.md) - Get running in 5 minutes
- [**Installation**](installation.md) - Detailed setup instructions
- [**Configuration**](configuration.md) - Configure for your domain

### Core Concepts
- [**Architecture Overview**](architecture.md) - How it all works together
- [**Entity Resolution**](entities.md) - Finding the right database records
- [**Route Patterns**](routing.md) - Flexible URL pattern matching
- [**LLM Integration**](llm.md) - Working with different language models

### API Reference
- [**REST API**](api.md) - Complete endpoint documentation
- [**Python Library**](python-api.md) - Core library reference
- [**Response Formats**](responses.md) - Understanding API responses

### Deployment
- [**Docker Deployment**](deployment/docker.md) - Production Docker setup
- [**Kubernetes**](deployment/kubernetes.md) - K8s deployment guide
- [**Environment Variables**](deployment/environment.md) - Configuration reference

### Guides
- [**Property Management Example**](guides/property-management.md) - Complete walkthrough
- [**E-commerce Integration**](guides/ecommerce.md) - Product catalog routing
- [**CRM System Setup**](guides/crm.md) - Customer management routing
- [**Custom Domain Setup**](guides/custom-domain.md) - Adapting to your domain

### Advanced
- [**Performance Optimization**](advanced/performance.md) - Scaling and speed tips
- [**Custom LLM Adapters**](advanced/custom-llm.md) - Build your own LLM integration
- [**Database Adapters**](advanced/database.md) - Custom database connectors
- [**Security**](advanced/security.md) - Authentication and authorization

## 🎯 Key Features

### 🧠 **LLM-Powered Intelligence**
- Support for GPT-4, Claude, Gemini, and local models
- Single-call optimization for 3x faster responses
- Intelligent entity resolution with confidence scoring

### 🔍 **Smart Entity Resolution**
- Fuzzy name matching across multiple database tables
- Context-aware entity disambiguation  
- Support for aliases and synonyms

### 🛣️ **Flexible Routing**
- Pattern-based URL generation
- Dynamic parameter resolution
- Support for complex nested routes

### 🔒 **Enterprise-Ready**
- Role-based access control (RBAC)
- Audit logging and performance monitoring
- Comprehensive error handling

### 🔌 **Pluggable Architecture**
- Multiple LLM providers (OpenAI, Anthropic, Google, Ollama)
- Database adapters (PostgreSQL, Supabase, more coming)
- Vector stores for semantic search (Faiss, Milvus)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │────│  FastAPI Server │────│   Core Router   │
│ "show me John"  │    │  (HTTP/JSON)    │    │  (LLM + Logic)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LLM Provider  │────│  Entity Resolver│
                       │ (GPT/Claude/..) │    │   (Database)    │
                       └─────────────────┘    └─────────────────┘
```

## 🌍 Use Cases

### Property Management
- *"Show me James Smith's monthly income"* → `/landlords/james-smith-123/financials`
- *"List vacant properties downtown"* → `/properties/search?status=vacant&location=downtown`

### E-commerce
- *"Find wireless headphones under $100"* → `/products/search?category=headphones&wireless=true&max_price=100`
- *"Show my recent orders"* → `/account/orders?recent=true`

### CRM Systems
- *"Edit Sarah's contact info"* → `/contacts/sarah-johnson-456/edit`
- *"Show deals closing this month"* → `/deals?closing_date=this_month`

## 🚀 Performance

- **🚀 < 1000ms**: Excellent (optimized single LLM call)
- **🏃 1000-3000ms**: Good (standard performance)
- **🐌 3000-5000ms**: Needs optimization
- **💩 5000-10000ms**: Slow (check configuration)
- **💀 > 10000ms**: RIP (debug required)

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](../CONTRIBUTING.md) for details.

## 📄 License

GNU General Public License v3 - see [LICENSE](../LICENSE) for details.

## 🆘 Support

- [GitHub Issues](https://github.com/yourusername/fantastic-router/issues)
- [Documentation](https://fantastic-router.readthedocs.io)
- [Discussions](https://github.com/yourusername/fantastic-router/discussions)

---

**Ready to get started?** → [Quick Start Guide](quickstart.md)
