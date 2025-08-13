# Production Deployment Guide

This guide explains how to deploy Fantastic Router in a production environment, moving beyond the example configurations to a proper production setup.

## 🏗️ Architecture Overview

### Development vs Production

| Component | Development | Production |
|-----------|-------------|------------|
| **Configuration** | `examples/quickstart/routes.json` | `configs/app.yaml` |
| **Database** | Local PostgreSQL | Managed PostgreSQL/Supabase |
| **LLM** | OpenAI API | Multiple providers + fallbacks |
| **Caching** | In-memory | Redis cluster |
| **Deployment** | Docker Compose | Kubernetes/Docker Swarm |
| **Monitoring** | Basic logs | Prometheus + Grafana |

## 📋 Prerequisites

### 1. Infrastructure Requirements

```bash
# Minimum requirements
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- Network: 100Mbps

# Recommended for production
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB SSD
- Network: 1Gbps
```

### 2. External Services

- **Database**: PostgreSQL 13+ or Supabase
- **Cache**: Redis 6+ (optional, falls back to memory)
- **LLM Provider**: OpenAI, Anthropic, or Google Gemini
- **Monitoring**: Prometheus + Grafana (optional)

## 🚀 Deployment Steps

### Step 1: Configuration Setup

1. **Copy the example configuration:**
```bash
cp configs/app.example.yaml configs/app.yaml
```

2. **Customize for your domain:**
```yaml
# Edit configs/app.yaml
site:
  domain: "your_domain"  # e.g., "ecommerce", "crm", "property_management"
  base_url: "https://your-app.com"
  
  # Define your entities
  entities:
    user:
      name: "user"
      table: "users"
      search_fields: ["name", "email"]
      
    product:
      name: "product" 
      table: "products"
      search_fields: ["name", "category"]
  
  # Define your route patterns
  route_patterns:
    - pattern: "/users/{user_id}"
      name: "user_profile"
      intent_patterns: ["show user {user}", "user {user} profile"]
```

### Step 2: Environment Variables

Create a `.env` file with your production secrets:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GEMINI_API_KEY=your-gemini-key

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# Cache Configuration
REDIS_URL=redis://redis-host:6379

# Security
JWT_SECRET=your-super-secret-jwt-key
API_KEY_1=your-api-key-1
API_KEY_2=your-api-key-2

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
```

### Step 3: Database Setup

#### Option A: PostgreSQL

```sql
-- Create database
CREATE DATABASE fantastic_router;

-- Create user
CREATE USER fantastic_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE fantastic_router TO fantastic_user;

-- Create tables (example for property management)
CREATE TABLE landlords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address TEXT NOT NULL,
    landlord_id UUID REFERENCES landlords(id),
    type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Option B: Supabase

1. Create a new Supabase project
2. Run the SQL above in the Supabase SQL editor
3. Get your project URL and API keys

### Step 4: Docker Deployment

#### Production Dockerfile

```dockerfile
# Use multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# Copy installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY packages/fantastic_router_server/ ./packages/fantastic_router_server/
COPY packages/fantastic_router_core/ ./packages/fantastic_router_core/
COPY adapters/ ./adapters/
COPY configs/ ./configs/

# Install application
RUN pip install -e "packages/fantastic_router_core[all]"
RUN pip install -e "packages/fantastic_router_server[production]"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8000
CMD ["uvicorn", "fantastic_router_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Production Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: fantastic_router_app
    environment:
      - CONFIG_FILE=/app/configs/app.yaml
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: fantastic_router_redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
```

### Step 5: Kubernetes Deployment

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fantastic-router
  labels:
    app: fantastic-router
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fantastic-router
  template:
    metadata:
      labels:
        app: fantastic-router
    spec:
      containers:
      - name: fantastic-router
        image: your-registry/fantastic-router:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONFIG_FILE
          value: "/app/configs/app.yaml"
        envFrom:
        - secretRef:
            name: fantastic-router-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fantastic-router-service
spec:
  selector:
    app: fantastic-router
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🔧 Configuration Management

### Environment-Specific Configs

```bash
configs/
├── app.yaml              # Production config
├── app.staging.yaml      # Staging config
├── app.development.yaml  # Development config
└── app.example.yaml      # Template
```

### Configuration Loading

The application loads configuration based on environment:

```python
# In your deployment
CONFIG_FILE=/app/configs/app.yaml uvicorn fantastic_router_server.main:app
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Basic health check
curl http://your-app.com/api/v1/health

# Detailed health check
curl http://your-app.com/api/v1/health/detailed
```

### Metrics Endpoint

```bash
# Prometheus metrics
curl http://your-app.com/api/v1/metrics
```

### Logging

Configure structured logging:

```yaml
monitoring:
  logging:
    level: "INFO"
    format: "json"
    output: "stdout"
```

## 🔒 Security Considerations

### 1. Authentication

```yaml
security:
  auth:
    enabled: true
    type: "jwt"
    jwt:
      secret: "${JWT_SECRET}"
      algorithm: "HS256"
      expires_in: 3600
```

### 2. Rate Limiting

```yaml
security:
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst_size: 20
```

### 3. Input Validation

```yaml
security:
  validation:
    max_query_length: 500
    max_context_size: 10000
```

## 🚀 Performance Optimization

### 1. Caching Strategy

```yaml
cache:
  type: "redis"
  redis:
    url: "${REDIS_URL}"
    request_ttl: 300      # 5 minutes
    structural_ttl: 1800  # 30 minutes
```

### 2. Database Optimization

```yaml
performance:
  database:
    connection_pool_size: 20
    query_timeout: 30
    enable_query_cache: true
```

### 3. LLM Optimization

```yaml
performance:
  llm:
    use_fast_planner: true
    single_call_optimization: true
    max_alternatives: 3
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy Fantastic Router

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t fantastic-router:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        docker tag fantastic-router:${{ github.sha }} your-registry/fantastic-router:latest
        docker push your-registry/fantastic-router:latest
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/fantastic-router fantastic-router=your-registry/fantastic-router:latest
        kubectl rollout status deployment/fantastic-router
```

## 🧪 Testing in Production

### Load Testing

```bash
# Install k6
curl -L https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz | tar xz

# Run load test
./k6 run load-test.js
```

### Load Test Script

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up
    { duration: '5m', target: 10 },  // Stay at 10
    { duration: '2m', target: 0 },   // Ramp down
  ],
};

export default function() {
  const payload = JSON.stringify({
    query: "show me user profile",
    user_id: "test-user",
    user_role: "user"
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = http.post('http://your-app.com/api/v1/plan', payload, params);
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });
}
```

## 🆘 Troubleshooting

### Common Issues

1. **Configuration not found**
   ```bash
   # Check config file path
   CONFIG_FILE=/app/configs/app.yaml
   ```

2. **Database connection failed**
   ```bash
   # Test database connection
   docker exec -it fantastic_router_app python -c "
   from adapters.db.postgres import create_postgres_client
   client = create_postgres_client()
   print(client.test_connection())
   "
   ```

3. **LLM API errors**
   ```bash
   # Check API keys
   echo $OPENAI_API_KEY
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```yaml
app:
  debug: true
  log_level: "DEBUG"
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale Kubernetes deployment
kubectl scale deployment fantastic-router --replicas=5

# Scale Docker Swarm service
docker service scale fantastic-router=5
```

### Vertical Scaling

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

This production setup provides a robust, scalable, and maintainable deployment of Fantastic Router! 🚀 