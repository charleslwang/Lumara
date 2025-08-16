"""
Configuration settings for the Lumara core pipeline.

This module provides configuration management for the Lumara pipeline,
with sensible defaults that can be overridden by environment variables.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

class PipelineConfig:
    """Configuration for the Lumara pipeline."""
    
    def __init__(self, **overrides):
        """Initialize configuration with optional overrides."""
        # Default configuration
        self.defaults = {
            # Core settings
            'debug': os.environ.get('LUMARA_DEBUG', 'false').lower() == 'true',
            'env': os.environ.get('LUMARA_ENV', 'development'),
            
            # Model settings
            'model_name': os.environ.get('LUMARA_MODEL', 'gemini-pro'),
            'max_iterations': int(os.environ.get('LUMARA_MAX_ITERATIONS', '3')),
            'temperature': float(os.environ.get('LUMARA_TEMPERATURE', '0.7')),
            
            # Paths
            'prompt_dir': str(Path(__file__).parent.parent / 'prompts'),
            
            # API settings
            'api_timeout': int(os.environ.get('LUMARA_API_TIMEOUT', '30')),
            'max_retries': int(os.environ.get('LUMARA_MAX_RETRIES', '3')),
            
            # Rate limiting
            'requests_per_minute': int(os.environ.get('LUMARA_RPM', '30')),
        }
        
        # Apply overrides
        self.config = {**self.defaults, **overrides}
    
    def __getattr__(self, name: str) -> Any:
        """Allow access to config values as attributes."""
        if name in self.config:
            return self.config[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with optional default."""
        return self.config.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return self.config.copy()


def get_config(**overrides) -> PipelineConfig:
    """Get a configuration instance with optional overrides."""
    return PipelineConfig(**overrides)


# Default configuration instance
config = get_config()
