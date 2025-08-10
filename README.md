# 🌟 Fantastic Router

<div align="center">
  <img src="assets/images/docs/fantastic-router.png" alt="Fantastic Router" height="120" />
</div>

> ⚠️ Warning: Fantastic Router is still in active development. Expect rapid changes, incomplete features, and the occasional bug while we build toward a stable release.

**An LLM-powered intent router for your website!**

Transform natural language queries into precise navigation actions. Instead of forcing users to navigate complex menus, let them simply say what they want: *"show me James Smith's monthly income"* → `/landlords/james-smith-123/financials`

## 🚀 What It Does

Fantastic Router uses Large Language Models to understand user intent and automatically route them to the right pages in your web application. It's like having an intelligent assistant that knows your entire application structure.

### Key Features

- **🧠 LLM-Powered**: Uses GPT-4, Claude, or local models to understand natural language
- **🔍 Smart Entity Resolution**: Finds the right database records contextually
- **🛣️ Pattern-Based Routing**: Flexible route patterns that adapt to any application
- **🔒 RBAC Integration**: Role-based access control built-in
- **🔌 Pluggable Architecture**: Works with any database, LLM provider, or vector store
- **📊 Domain Agnostic**: Property management, e-commerce, CRM, healthcare - works anywhere

## 🎯 Use Cases

Perfect for applications with:
- **Complex navigation hierarchies** (enterprise software, admin panels)
- **Deep data relationships** (CRM systems, property management)
- **User experience bottlenecks** (users can't find what they need)
- **Search limitations** (traditional search isn't contextual enough)

## 🏗️ Architecture

```
User Query: "show me James Smith's income"
    ↓
🧠 Intent Parser (LLM) → Understands: action=NAVIGATE, entity=James Smith, view=income
    ↓
🔍 Entity Resolver → Finds: james-smith-123 in landlords table
    ↓
🛣️ Route Matcher (LLM) → Matches: /{entity_type}/{entity_id}/{view_type}
    ↓
📍 Action Plan → Result: /landlords/james-smith-123/financials
```

## 🚀 Quick Start

### Option 1: Try it Now with Docker (Recommended)

The fastest way to test Fantastic Router is with our Docker setup that includes a real database and sample data:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/fantastic-router
cd fantastic-router

# 2. Set up everything (database, sample data, dependencies)
make setup

# 3. Add your OpenAI API key
cp docker/.env.example docker/.env
# Edit docker/.env and add your OpenAI API key

# 4. Test with mock data (works without API key)
make test

# 5. Test with real database and LLM
make test-real
```

**Available Make Commands:**
```bash
make help        # Show all available commands
make up          # Start all services (app + database)
make up-db       # Start only the database
make test        # Run test with mock data
make test-real   # Run test with real database + LLM
make test-db     # Check database connection and data
make shell       # Open shell in app container
make db-shell    # Open PostgreSQL shell
make clean       # Clean up containers and volumes
```

### Option 2: Manual Installation (still testing this, proceed with caution)

```bash
# Core library
pip install fantastic-router-core

# With OpenAI support
pip install fantastic-router-core[openai]

# With PostgreSQL support  
pip install fantastic-router-core[postgres]

# Everything
pip install fantastic-router-core[all]
```

### Basic Usage

```python
import asyncio
from fantastic_router_core import FantasticRouter
from fantastic_router_core.adapters.llm.openai import OpenAILLMClient
from fantastic_router_core.adapters.db.postgres import PostgreSQLDatabaseClient

async def main():
    # Set up LLM client
    llm_client = OpenAILLMClient(api_key="your-openai-key")
    
    # Set up database client
    db_client = PostgreSQLDatabaseClient(
        connection_string="postgresql://user:pass@localhost/db"
    )
    
    # Load configuration
    router = await FantasticRouter.from_config(
        config_path="routes.json",
        llm_client=llm_client,
        db_client=db_client
    )
    
    # Route a query
    action = await router.plan("show me James Smith's income")
    print(f"Route: {action.route}")  # /landlords/james-smith-123/financials
    print(f"Confidence: {action.confidence}")  # 0.94
```

## 🧪 Docker Development Environment

The included Docker setup provides:
- **PostgreSQL database** with realistic sample data
- **Automatic schema setup** with users, landlords, tenants, properties
- **pgAdmin interface** for database management (`http://localhost:8080`)
- **Live code reloading** for development
- **Mock LLM responses** when no API key is provided

**Sample data includes:**
- James Smith (landlord with $4,500 monthly income)
- Sarah Johnson (landlord with $3,200 monthly income)  
- John Doe, Emily Davis, Michael Brown (tenants)
- Real properties with addresses and lease agreements

## ⚙️ Configuration

Create a `routes.json` file:

```json
{
  "domain": "property_management",
  "base_url": "https://myapp.com",
  "route_patterns": [
    {
      "pattern": "/{entity_type}/{entity_id}/{view_type}",
      "name": "entity_detail_view",
      "description": "View specific details for an entity",
      "intent_patterns": [
        "show {entity} {view_data}",
        "view {entity} {view_data}",
        "see {entity} {view_data}"
      ],
      "parameters": {
        "entity_type": {
          "type": "string",
          "description": "Type of entity (landlords, tenants, properties)",
          "examples": ["landlords", "tenants", "properties"]
        },
        "entity_id": {
          "type": "string", 
          "description": "Unique identifier for the entity"
        },
        "view_type": {
          "type": "string",
          "description": "Type of data to view",
          "examples": ["financials", "contact", "overview"]
        }
      }
    }
  ],
  "entities": {
    "person": {
      "table": "users",
      "search_fields": ["name", "email"],
      "display_field": "name"
    }
  },
  "database_schema": {
    "tables": {
      "users": {
        "columns": [
          {"name": "id", "type": "uuid"},
          {"name": "name", "type": "varchar"},
          {"name": "email", "type": "varchar"}
        ]
      },
      "landlords": {
        "columns": [
          {"name": "id", "type": "uuid"},
          {"name": "user_id", "type": "uuid"},
          {"name": "monthly_income", "type": "decimal"}
        ]
      }
    },
    "relationships": {
      "landlords.user_id": "users.id"
    }
  }
}
```

## 🎨 Example Queries

Once configured, your router understands queries like:

```python
# Navigation
await router.plan("show me James Smith's monthly income")
# → /landlords/james-smith-123/financials

await router.plan("view tenant contact info for John Doe") 
# → /tenants/john-doe-456/contact

# CRUD operations
await router.plan("create new property")
# → /properties/create

await router.plan("edit Sarah's information")
# → /users/sarah-wilson-789/edit

# Listing and search
await router.plan("show all properties")
# → /properties

await router.plan("search for properties in downtown")
# → /properties/search?q=downtown
```

## 🔧 Advanced Features

### Custom LLM Providers

```python
from fantastic_router_core.planning.intent_parser import LLMClient

class CustomLLMClient:
    async def analyze(self, prompt: str, temperature: float = 0.1):
        # Your custom LLM implementation
        return {"action_type": "NAVIGATE", "entities": ["James Smith"]}

router = FantasticRouter(
    llm_client=CustomLLMClient(),
    db_client=db_client,
    config=config
)
```

### Database Adapters

```python
from fantastic_router_core.retrieval.vector import DatabaseClient

class CustomDatabaseClient:
    async def search(self, query: str, tables: List[str], fields: List[str]):
        # Your custom database search implementation
        return [{"id": "123", "name": "James Smith"}]
```

### RBAC Integration (work in progress)

```python
action = await router.plan(
    "show sensitive financial data", 
    user_role="admin"  # Only admins can access certain routes
)
```

<!-- Not setup -->
<!-- ## 🏢 Enterprise Features

The enterprise version includes:

- **📈 Learning & Adaptation**: Improves accuracy over time based on usage
- **📊 Analytics Dashboard**: Query success rates, performance metrics
- **🔧 Custom Domain Training**: Train the router on your specific domain
- **🏗️ On-Premise Deployment**: Keep your data secure
- **📞 Priority Support**: Dedicated support team -->

<!-- ## 🛣️ Roadmap

- [ ] **v0.2**: Web UI for configuration management
- [ ] **v0.3**: Semantic search with vector embeddings  
- [ ] **v0.4**: Multi-language support
- [ ] **v0.5**: GraphQL API integration
- [ ] **v1.0**: Production-ready with enterprise features -->

## 🤝 Contributing

We welcome contributions! 
<!-- See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. -->

### Development Setup

**Quick Setup with Docker:**
```bash
git clone https://github.com/yourusername/fantastic-router
cd fantastic-router
make setup          # Sets up everything
make test-real      # Run tests
```

**Manual Setup:**
```bash
git clone https://github.com/yourusername/fantastic-router
cd fantastic-router
pip install -e "packages/fantastic_router_core[dev]"
pytest
```

**Useful Development Commands:**
```bash
make shell          # Open development shell
make db-shell       # Access database directly
make logs           # View application logs
make clean          # Reset everything
```

## 📄 License

GNU General Public License v3 (GPLv3) - see [LICENSE](LICENSE) for details.

## 🙋‍♂️ Support

<!-- - **Documentation**: [https://fantastic-router.readthedocs.io](https://fantastic-router.readthedocs.io) -->
- **Issues**: [GitHub Issues](https://github.com/yourusername/fantastic-router/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fantastic-router/discussions)
<!-- - **Enterprise**: [Contact Sales](mailto:sales@fantastic-router.com) -->

---

**Made with ❤️ by developers who believe navigation should be intuitive.**
