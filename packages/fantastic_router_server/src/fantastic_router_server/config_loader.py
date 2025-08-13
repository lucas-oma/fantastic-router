"""
Configuration loader for Fantastic Router
Handles YAML config files with environment variable substitution
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Loads and processes configuration files with environment variable substitution"""
    
    def __init__(self):
        self.config_cache: Dict[str, Any] = {}
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file with environment variable substitution
        
        Args:
            config_path: Path to config file. If None, tries default locations
            
        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = self._find_config_file()
        
        if config_path in self.config_cache:
            return self.config_cache[config_path]
        
        # Load and process the config file
        config_data = self._load_yaml_with_env_substitution(config_path)
        self.config_cache[config_path] = config_data
        return config_data
    
    def _find_config_file(self) -> str:
        """Find the appropriate config file to load"""
        config_paths = [
            # Production config paths (prioritize YAML)
            "/app/configs/app.yaml",
            "/app/configs/app.yml",
            "/app/configs/app.example.yaml",
            "/app/configs/app.example.yml",
            
            # Legacy JSON paths
            "/app/examples/quickstart/routes.json",
            "/app/routes.json",
            "examples/quickstart/routes.json",
            "routes.json"
        ]
        
        for path in config_paths:
            if Path(path).exists():
                return path
        
        raise FileNotFoundError("No configuration file found")
    
    def _load_yaml_with_env_substitution(self, config_path: str) -> Dict[str, Any]:
        """Load YAML file and substitute environment variables"""
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Substitute environment variables
        processed_content = self._substitute_env_vars(content)
        
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            config_data = yaml.safe_load(processed_content)
            # Return full config for YAML files (includes llm, database, etc.)
            return config_data
        else:
            import json
            return json.loads(processed_content)
    
    def _substitute_env_vars(self, content: str) -> str:
        """Substitute environment variables in string content"""
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_env_var(match):
            var_expr = match.group(1)
            
            # Check if there's a default value
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(var_expr, '')
        
        return re.sub(pattern, replace_env_var, content)


# Global config loader instance
_config_loader = ConfigLoader()


def get_config() -> Dict[str, Any]:
    """Get application configuration"""
    return _config_loader.load_config()


def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from YAML"""
    config = _config_loader.load_config()
    return config.get('llm', {})


def get_database_config() -> Dict[str, Any]:
    """Get database configuration from YAML"""
    config = _config_loader.load_config()
    return config.get('database', {}) 