-- Fantastic Router System Database
-- This database manages API keys, users, authentication, and system-level data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and user management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- admin, user, api_user
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table for managing API access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
               api_key VARCHAR(255) UNIQUE NOT NULL, -- Stored as plain text for simplicity
    permissions JSONB DEFAULT '{}', -- Store permissions as JSON
    rate_limit_per_minute INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- LLM Provider Configuration table
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_name VARCHAR(50) NOT NULL, -- openai, anthropic, gemini, ollama
    api_key_hash VARCHAR(255) NOT NULL,
    base_url VARCHAR(255),
    model_name VARCHAR(100),
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}', -- Store provider-specific config
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Domain Configurations table
CREATE TABLE domain_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_name VARCHAR(100) UNIQUE NOT NULL, -- property_management, ecommerce, etc.
    config_data JSONB NOT NULL, -- Store the full YAML config as JSON
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Request Logs table for monitoring and analytics
CREATE TABLE request_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    api_key_id UUID REFERENCES api_keys(id),
    query TEXT NOT NULL,
    domain VARCHAR(100),
    route VARCHAR(255),
    confidence DECIMAL(3,2),
    duration_ms INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    cache_type VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rate Limiting table
CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES api_keys(id),
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(api_key_id, window_start)
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(api_key);
CREATE INDEX idx_llm_providers_name ON llm_providers(provider_name);
CREATE INDEX idx_domain_configs_name ON domain_configs(domain_name);
CREATE INDEX idx_request_logs_user_id ON request_logs(user_id);
CREATE INDEX idx_request_logs_created_at ON request_logs(created_at);
CREATE INDEX idx_rate_limits_api_key_window ON rate_limits(api_key_id, window_start);

-- Insert default admin user
INSERT INTO users (username, email, password_hash, full_name, role) VALUES 
('admin', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i', 'System Administrator', 'admin');

-- Insert default LLM providers (with placeholder API keys)
INSERT INTO llm_providers (provider_name, api_key_hash, model_name, is_default, config) VALUES 
('openai', '$2b$12$placeholder', 'gpt-3.5-turbo-1106', true, '{"temperature": 0.1, "max_tokens": 1000}'),
('anthropic', '$2b$12$placeholder', 'claude-3-haiku-20240307', false, '{"temperature": 0.1, "max_tokens": 1000}'),
('gemini', '$2b$12$placeholder', 'gemini-1.5-flash', false, '{"temperature": 0.1, "max_tokens": 1000}'),
('ollama', '$2b$12$placeholder', 'llama3.1:8b', false, '{"base_url": "http://localhost:11434", "temperature": 0.1}');

-- Insert default domain configuration
INSERT INTO domain_configs (domain_name, config_data, created_by) VALUES 
('property_management', '{"domain": "property_management", "entities": {}, "routes": []}', (SELECT id FROM users WHERE username = 'admin'));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_llm_providers_updated_at BEFORE UPDATE ON llm_providers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_domain_configs_updated_at BEFORE UPDATE ON domain_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 