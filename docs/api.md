# REST API Reference

Complete documentation for the Fantastic Router REST API.

## Base URL

```
http://localhost:8000    # Development
https://your-domain.com  # Production
```

## Authentication

Currently, the API supports API key authentication (planned). For development, no authentication is required.

```bash
# Future authentication
curl -H "Authorization: Bearer your-api-key" \
     https://your-domain.com/api/v1/plan
```

## Content Type

All requests and responses use JSON:
```
Content-Type: application/json
```

## 🎯 Core Endpoints

### POST `/api/v1/plan`

**Purpose**: Transform natural language queries into structured routing actions.

#### Request Format

```json
{
  "query": "show me James Smith monthly income",
  "user_id": "user-123",
  "user_role": "admin", 
  "context": {
    "current_page": "/dashboard",
    "filters": {"department": "sales"}
  },
  "max_alternatives": 3
}
```

**Parameters**:
- `query` *(required)*: Natural language query (1-500 characters)
- `user_id` *(optional)*: User identifier for personalization
- `user_role` *(optional)*: User role for RBAC filtering
- `context` *(optional)*: Additional context object
- `max_alternatives` *(optional)*: Number of alternative routes (0-10, default: 3)

#### Response Format

```json
{
  "success": true,
  "action_plan": {
    "action_type": "NAVIGATE",
    "route": "/landlords/efb6d2e1-8944-40f8-bcf3-f82737873542/financials",
    "confidence": 0.87,
    "reasoning": "User wants to navigate to James Smith's financial information...",
    "parameters": [
      {
        "name": "entity_type",
        "value": "landlords",
        "type": "string",
        "source": "inferred"
      },
      {
        "name": "entity_id", 
        "value": "efb6d2e1-8944-40f8-bcf3-f82737873542",
        "type": "string",
        "source": "entity"
      },
      {
        "name": "view_type",
        "value": "financials", 
        "type": "string",
        "source": "inferred"
      }
    ],
    "entities": [
      {
        "id": "efb6d2e1-8944-40f8-bcf3-f82737873542",
        "name": "James Smith",
        "table": "users",
        "confidence": 0.95,
        "metadata": {
          "id": "efb6d2e1-8944-40f8-bcf3-f82737873542", 
          "name": "James Smith",
          "email": "james.smith@example.com",
          "role": "landlord"
        }
      }
    ],
    "query_params": {},
    "matched_pattern": "/{entity_type}/{entity_id}/{view_type}"
  },
  "alternatives": [],
  "performance": {
    "duration_ms": 2971.65,
    "level": "good",
    "llm_calls": 1,
    "cache_hits": 0
  },
  "metadata": {
    "query_length": 34,
    "user_id": null,
    "user_role": null,
    "timestamp": 1754718420.1642342
  }
}
```

#### Action Types

- `NAVIGATE`: Go to a specific page/view
- `CREATE`: Create a new resource
- `EDIT`: Edit an existing resource
- `DELETE`: Delete a resource
- `QUERY`: Search or filter data

#### Performance Levels

- **🚀 excellent** (< 1000ms): Optimized performance
- **🏃 good** (1000-3000ms): Standard performance  
- **🐌 acceptable** (3000-5000ms): Needs optimization
- **💩 slow** (5000-10000ms): Performance issues
- **💀 rip** (> 10000ms): Critical issues

#### Example Requests

**Property Management Examples**:
```bash
# Navigate to specific entity
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "show me James Smith monthly income"}'

# Create new resource
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "create new property"}'

# Search with filters
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "list vacant properties downtown"}'
```

**E-commerce Examples**:
```bash
# Product search
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "find wireless headphones under $100"}'

# User account navigation
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "show my recent orders"}'
```

### GET `/api/v1/health`

**Purpose**: Check system health and component status.

#### Response Format

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "database": "healthy",
    "llm": "available", 
    "configuration": "loaded"
  },
  "timestamp": 1754718054.3533673
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some components have issues
- `unhealthy`: Critical systems down

**Component Status**:
- `healthy`: Component is working normally
- `available`: Component is accessible
- `mock`: Using mock/test version
- `error: <message>`: Component has issues
- `unknown`: Status cannot be determined

### GET `/api/v1/stats`

**Purpose**: Get usage and performance statistics.

#### Response Format

```json
{
  "requests_total": 1247,
  "avg_response_time_ms": 1850.5,
  "avg_confidence": 0.84,
  "top_queries": [
    "show me properties",
    "create new tenant", 
    "edit contact info"
  ],
  "error_rate": 0.02,
  "uptime_seconds": 86400
}
```

## 🏠 Health & Info Endpoints

### GET `/`

**Purpose**: Root endpoint with basic information.

```json
{
  "name": "Fantastic Router",
  "version": "0.1.0", 
  "edition": "COMMUNITY",
  "message": "LLM-powered intent router for web applications",
  "docs": "/docs",
  "health": "/health"
}
```

### GET `/ping`

**Purpose**: Simple connectivity test.

```json
{
  "status": "pong"
}
```

### GET `/version`

**Purpose**: Version information.

```json
{
  "version": "0.1.0",
  "edition": "COMMUNITY", 
  "name": "Fantastic Router"
}
```

### GET `/about`

**Purpose**: Detailed application information.

```json
{
  "name": "Fantastic Router",
  "edition": "COMMUNITY",
  "version": "0.1.0",
  "description": "LLM-powered intent router for web applications"
}
```

## 📋 Interactive Documentation

### GET `/docs`

**Purpose**: Swagger UI for interactive API exploration.

- Test endpoints directly in the browser
- View request/response schemas
- Generate example requests
- Download OpenAPI specification

### GET `/redoc`

**Purpose**: Alternative documentation interface.

- Clean, readable format
- Detailed schema information
- Code examples in multiple languages

### GET `/openapi.json`

**Purpose**: Raw OpenAPI specification.

- Machine-readable API definition
- Use for client SDK generation
- Integration with API tools

## ❌ Error Responses

### Error Format

```json
{
  "detail": {
    "error": "Planning failed", 
    "message": "'dict' object has no attribute 'domain'",
    "duration_ms": 0.13
  }
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Authentication required (future)
- `403 Forbidden`: Insufficient permissions (future)
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded (future)
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: System overloaded

### Common Errors

**Invalid Query**:
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Query Too Long**:
```json
{
  "detail": [
    {
      "loc": ["body", "query"], 
      "msg": "ensure this value has at most 500 characters",
      "type": "value_error.any_str.max_length",
      "ctx": {"limit_value": 500}
    }
  ]
}
```

**Planning Failed**:
```json
{
  "detail": {
    "error": "Planning failed",
    "message": "LLM timeout after 60 seconds", 
    "duration_ms": 60000.0
  }
}
```

## 🔧 Request Examples

### cURL Examples

**Basic Planning Request**:
```bash
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{
    "query": "show me John Doe contact information",
    "user_role": "admin"
  }'
```

**Planning with Context**:
```bash
curl -X POST http://localhost:8000/api/v1/plan \
  -H "Content-Type: application/json" \
  -d '{
    "query": "edit this property",
    "user_id": "user-123",
    "context": {
      "current_page": "/properties/abc-123", 
      "property_id": "abc-123"
    }
  }'
```

**Health Check**:
```bash
curl http://localhost:8000/api/v1/health
```

### JavaScript Examples

**Using Fetch API**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/plan', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'show me recent sales reports',
    user_role: 'manager'
  })
});

const result = await response.json();
console.log(result.action_plan.route);
```

**Using Axios**:
```javascript
import axios from 'axios';

const planRoute = async (query, userRole = null) => {
  try {
    const response = await axios.post('http://localhost:8000/api/v1/plan', {
      query,
      user_role: userRole,
      max_alternatives: 2
    });
    
    return response.data.action_plan;
  } catch (error) {
    console.error('Planning failed:', error.response.data);
    throw error;
  }
};

// Usage
const actionPlan = await planRoute('create new tenant', 'admin');
window.location.href = actionPlan.route;
```

### Python Examples

**Using requests**:
```python
import requests

def plan_route(query: str, user_role: str = None) -> dict:
    response = requests.post('http://localhost:8000/api/v1/plan', json={
        'query': query,
        'user_role': user_role
    })
    response.raise_for_status()
    return response.json()

# Usage
result = plan_route('show me property maintenance requests')
print(f"Route: {result['action_plan']['route']}")
print(f"Confidence: {result['action_plan']['confidence']}")
```

**Using httpx (async)**:
```python
import httpx
import asyncio

async def plan_route_async(query: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post('http://localhost:8000/api/v1/plan', json={
            'query': query
        })
        response.raise_for_status()
        return response.json()

# Usage
async def main():
    result = await plan_route_async('edit Sarah Johnson profile')
    print(result['action_plan']['route'])

asyncio.run(main())
```

## 🚀 Rate Limiting (Future)

**Planned Rate Limits**:
- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1,000 requests/hour  
- **Enterprise**: Unlimited

**Rate Limit Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 842
X-RateLimit-Reset: 1609459200
```

## 🔐 Authentication (Future)

**API Key Authentication**:
```bash
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/v1/plan
```

**JWT Authentication**:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     http://localhost:8000/api/v1/plan
```

---

**Next**: [Python Library Reference](python-api.md) | **Previous**: [Architecture](architecture.md)
