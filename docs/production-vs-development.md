# Development vs Production Setup

This document explains the key differences between development and production environments for Fantastic Router.

## 🏗️ Architecture Comparison

| Component | Development | Production |
|-----------|-------------|------------|
| **Purpose** | Testing & Development | Live Service |
| **Users** | Developers | End Users |
| **Scale** | Single instance | Multiple instances |
| **Data** | Mock/Sample data | Real production data |
| **Security** | Basic | Enterprise-grade |

## 📁 Configuration Files

### Development Setup
```
fantastic-router/
├── examples/quickstart/
│   ├── routes.json          # Simple domain config
│   ├── example.py           # Basic test script
│   └── test_*.py            # Individual test scripts
├── docker/
│   └── docker-compose.yml   # Development services
└── Makefile                 # Development commands
```

### Production Setup
```
fantastic-router/
├── configs/
│   ├── app.yaml             # Production config
│   ├── app.staging.yaml     # Staging config
│   └── app.example.yaml     # Template
├── docker-compose.prod.yml  # Production services
├── Makefile.prod            # Production commands
├── .env                     # Production secrets
└── scripts/
    ├── setup-production.sh  # Setup script
    ├── monitor.sh           # Health monitoring
    └── backup.sh            # Database backup
```

## 🔧 Configuration Differences

### Development Configuration (`examples/quickstart/routes.json`)
```json
{
  "domain": "property_management",
  "base_url": "http://localhost:8000",
  "entities": {
    "landlord": {
      "name": "landlord",
      "table": "landlords",
      "search_fields": ["name", "email"]
    }
  },
  "route_patterns": [
    {
      "pattern": "/landlords/{landlord_id}/properties",
      "name": "landlord_properties",
      "intent_patterns": ["show {landlord} properties"]
    }
  ]
}
```

### Production Configuration (`configs/app.yaml`)
```yaml
# Application Settings
app:
  name: "Fantastic Router"
  environment: "production"
  debug: false
  log_level: "INFO"
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins: ["https://yourdomain.com"]
  rate_limit_per_minute: 100

# LLM Provider Configuration
llm:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"
    max_tokens: 1000
    temperature: 0.1

# Database Configuration
database:
  type: "postgres"
  postgres:
    url: "${DATABASE_URL}"
    max_connections: 20
    restricted_tables: ["users_passwords", "sessions"]
    allowed_tables: ["users", "properties", "tenants"]

# Site Configuration
site:
  domain: "your_domain"
  base_url: "https://your-app.com"
  entities:
    user:
      name: "user"
      table: "users"
      search_fields: ["name", "email"]
  route_patterns:
    - pattern: "/users/{user_id}"
      name: "user_profile"
      intent_patterns: ["show user {user}"]

# Caching Configuration
cache:
  type: "redis"
  redis:
    url: "${REDIS_URL}"
    request_ttl: 300
    structural_ttl: 1800

# Security Configuration
security:
  auth:
    enabled: true
    type: "jwt"
    jwt:
      secret: "${JWT_SECRET}"
  rate_limit:
    enabled: true
    requests_per_minute: 100

# Monitoring Configuration
monitoring:
  enabled: true
  metrics:
    enabled: true
  logging:
    level: "INFO"
    format: "json"
```

## 🐳 Deployment Differences

### Development Deployment
```bash
# Simple development setup
make up                    # Start services
make test-server          # Test endpoints
make test-caching         # Test caching
make down                 # Stop services
```

### Production Deployment
```bash
# Production setup
./scripts/setup-production.sh  # Initial setup
make -f Makefile.prod up      # Start production services
./scripts/monitor.sh          # Monitor health
make -f Makefile.prod backup  # Backup database
```

## 🔐 Security Differences

| Security Aspect | Development | Production |
|-----------------|-------------|------------|
| **Authentication** | None | JWT/API Keys |
| **Rate Limiting** | None | 100 req/min |
| **CORS** | Allow all | Specific domains |
| **Database Access** | Full access | Restricted tables |
| **Logging** | Basic | Structured JSON |
| **Secrets** | Hardcoded | Environment variables |

## 📊 Performance Differences

| Performance Aspect | Development | Production |
|-------------------|-------------|------------|
| **Caching** | In-memory | Redis cluster |
| **Database** | Local PostgreSQL | Managed PostgreSQL |
| **LLM Calls** | Single provider | Multiple providers + fallbacks |
| **Workers** | 1 | 4+ workers |
| **Monitoring** | Basic logs | Prometheus + Grafana |
| **Backup** | None | Automated daily |

## 🚀 Migration Path

### Step 1: Setup Production Environment
```bash
# Run production setup script
./scripts/setup-production.sh
```

### Step 2: Customize Configuration
```bash
# Edit production config
nano configs/app.yaml

# Add your secrets
nano .env
```

### Step 3: Deploy
```bash
# Build and start production services
make -f Makefile.prod build
make -f Makefile.prod up
```

### Step 4: Verify
```bash
# Check health
./scripts/monitor.sh

# Test endpoints
curl http://localhost:8000/api/v1/health
```

## 🔄 Environment Management

### Development Workflow
```bash
# Start development
make up

# Make changes
# Test changes
make test-server

# Stop development
make down
```

### Production Workflow
```bash
# Deploy to staging
make -f Makefile.prod -e ENV=staging up

# Test staging
./scripts/monitor.sh

# Deploy to production
make -f Makefile.prod -e ENV=production up

# Monitor production
./scripts/monitor.sh
```

## 📈 Scaling Considerations

### Development Scaling
- Single instance
- Local resources
- Manual scaling

### Production Scaling
- Multiple instances
- Load balancer
- Auto-scaling
- Database clustering
- Redis clustering

## 🛠️ Maintenance

### Development Maintenance
```bash
# Update dependencies
pip install -r requirements.txt

# Restart services
make down && make up
```

### Production Maintenance
```bash
# Zero-downtime deployment
make -f Makefile.prod deploy

# Database migrations
make -f Makefile.prod migrate

# Backup before updates
make -f Makefile.prod backup

# Monitor after updates
./scripts/monitor.sh
```

## 🎯 Key Takeaways

1. **Development** is for testing and iteration
2. **Production** is for reliability and scale
3. **Configuration** becomes more complex but more powerful
4. **Security** is critical in production
5. **Monitoring** is essential for production
6. **Backup** and recovery are production requirements
7. **Automation** reduces human error in production

The production setup provides enterprise-grade features while maintaining the simplicity of the development environment! 🚀 