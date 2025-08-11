# YAML Configuration Migration Guide

This document describes the migration from environment variable-based configuration to a centralized YAML configuration system for Fantastic Router.

## Overview

Fantastic Router now uses a comprehensive YAML configuration file (`configs/app.yaml`) that centralizes all configuration settings, including environment variable substitution for sensitive data like API keys.

## Migration Summary

### Before: Environment Variables
Previously, configuration was scattered across multiple environment variables:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-3.5-turbo-1106
OPENAI_MAX_TOKENS=1000
GEMINI_API_KEY=your-google-ai-api-key-here
GEMINI_MODEL=gemini-1.5-flash
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Database Configuration
DATABASE_URL=postgresql://fantastic_user:fantastic_pass@postgres:5432/property_mgmt
DB_MAX_CONNECTIONS=10
DB_TIMEOUT=30

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
USE_FAST_PLANNER=true
LLM_TIMEOUT=60
LLM_TEMPERATURE=0.1
```

### After: YAML Configuration
Now all configuration is centralized in `configs/app.yaml`:

```yaml
# Application metadata
app:
  domain: "property_management"
  base_url: "https://myapp.com"
  version: "1.0.0"
  environment: "${APP_ENV:-development}"
  use_fast_planner: "${USE_FAST_PLANNER:-true}"

# Database configuration
database:
  type: "direct"  # or "api"
  connection_string: "${DATABASE_URL}"
  max_connections: "${DB_MAX_CONNECTIONS:-10}"
  timeout: "${DB_TIMEOUT:-30}"

# LLM configuration
llm:
  provider: "openai"  # or "anthropic", "gemini", "ollama"
  model: "${OPENAI_MODEL:-gpt-3.5-turbo-1106}"
  temperature: 0.1
  max_tokens: "${OPENAI_MAX_TOKENS:-1000}"
  api_key: "${OPENAI_API_KEY}"
  timeout: "${LLM_TIMEOUT:-60}"
  
  # Alternative LLM providers
  gemini:
    api_key: "${GEMINI_API_KEY}"
    model: "${GEMINI_MODEL:-gemini-1.5-flash}"
  
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "${ANTHROPIC_MODEL:-claude-3-haiku-20240307}"
  
  ollama:
    base_url: "${OLLAMA_BASE_URL:-http://localhost:11434}"
    model: "${OLLAMA_MODEL:-llama3.1:8b}"

# Logging configuration
logging:
  level: "${LOG_LEVEL:-INFO}"
  format: "json"
  output: "stdout"
  include_timestamps: true
```

## Key Benefits

### 1. **Centralized Configuration**
- All settings in one place
- Clear structure and organization
- Easy to understand and modify

### 2. **Environment Variable Substitution**
- Secure credential management with `${VAR_NAME}` syntax
- Default values with `${VAR_NAME:-default}` syntax
- Maintains security best practices

### 3. **Production Ready**
- Structured, hierarchical configuration
- Comprehensive sections for all components
- Easy to manage in containerized environments

### 4. **Backward Compatibility**
- Still supports legacy JSON configurations
- Automatic fallback mechanisms
- Gradual migration path

## Environment Variable Mapping

| Environment Variable | YAML Path | Default Value |
|---------------------|-----------|---------------|
| `OPENAI_API_KEY` | `llm.api_key` | Required |
| `OPENAI_MODEL` | `llm.model` | `gpt-3.5-turbo-1106` |
| `OPENAI_MAX_TOKENS` | `llm.max_tokens` | `1000` |
| `GEMINI_API_KEY` | `llm.gemini.api_key` | Required |
| `GEMINI_MODEL` | `llm.gemini.model` | `gemini-1.5-flash` |
| `ANTHROPIC_API_KEY` | `llm.anthropic.api_key` | Required |
| `ANTHROPIC_MODEL` | `llm.anthropic.model` | `claude-3-haiku-20240307` |
| `OLLAMA_BASE_URL` | `llm.ollama.base_url` | `http://localhost:11434` |
| `OLLAMA_MODEL` | `llm.ollama.model` | `llama3.1:8b` |
| `DATABASE_URL` | `database.connection_string` | Required |
| `DB_MAX_CONNECTIONS` | `database.max_connections` | `10` |
| `DB_TIMEOUT` | `database.timeout` | `30` |
| `APP_ENV` | `app.environment` | `development` |
| `LOG_LEVEL` | `logging.level` | `INFO` |
| `USE_FAST_PLANNER` | `app.use_fast_planner` | `true` |
| `LLM_TIMEOUT` | `llm.timeout` | `60` |
| `LLM_TEMPERATURE` | `llm.temperature` | `0.1` |

## Configuration Loading Priority

The system loads configuration in the following order:

1. **YAML Configuration** (`configs/app.yaml`) - **Primary**
2. **Legacy JSON Configuration** (`routes.json`) - **Fallback**
3. **Environment Variables** - **Emergency Fallback**

## Docker Integration

The Docker setup automatically mounts the `configs` directory and provides environment variables for substitution:

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - PYTHONPATH=/app
      # Environment variables for YAML config substitution
      - DATABASE_URL=postgresql://fantastic_user:fantastic_pass@postgres:5432/property_mgmt
      - OPENAI_API_KEY=${OPENAI_API_KEY:-your-openai-api-key-here}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-3.5-turbo-1106}
      # ... more environment variables
    volumes:
      - ../configs:/app/configs
```

## Testing

Use the provided test scripts to verify configuration:

```bash
# Test YAML configuration loading
python examples/quickstart/test_yaml_config.py

# Test environment variable substitution
python examples/quickstart/test_env_substitution.py

# Test in Docker
docker exec fantastic_router_app python /app/examples/quickstart/test_yaml_config.py
```

## Migration Steps

1. **Update Configuration File**: Modify `configs/app.yaml` with your settings
2. **Set Environment Variables**: Ensure required environment variables are set
3. **Update Docker Compose**: Environment variables are automatically provided
4. **Test Configuration**: Run test scripts to verify everything works
5. **Deploy**: The system will automatically use YAML configuration

## Security Considerations

- **API Keys**: Never commit real API keys to version control
- **Environment Variables**: Use environment variables for sensitive data
- **Default Values**: Provide safe defaults for non-sensitive settings
- **Validation**: The system validates configuration on startup

## Troubleshooting

### Common Issues

1. **Configuration Not Found**: Ensure `configs/app.yaml` exists and is mounted in Docker
2. **Environment Variables Not Substituted**: Check that environment variables are set correctly
3. **LLM Client Not Created**: Verify API keys are provided and valid
4. **Database Connection Failed**: Check database URL and credentials

### Debug Commands

```bash
# Check configuration loading
docker exec fantastic_router_app python -c "from fantastic_router_server.config_loader import get_config; print(get_config())"

# Check LLM client creation
docker exec fantastic_router_app python -c "from fantastic_router_server.api.deps import DependencyContainer; print(type(DependencyContainer().llm_client))"

# Check health endpoint
curl http://localhost:8000/api/v1/health
```

## Conclusion

The YAML configuration system provides a more maintainable, secure, and production-ready approach to configuration management. It centralizes all settings while maintaining the flexibility of environment variable substitution for sensitive data. 