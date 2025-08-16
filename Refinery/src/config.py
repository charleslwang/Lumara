import os
from typing import Dict, Any

# API key will be provided by user per request
# No environment validation needed for stateless deployment

# Gemini model configuration
# Using gemini-2.5-flash for faster response times
MODEL_NAME = 'gemini-2.5-flash'

# Generation configuration for consistent behavior
GENERATION_CONFIG: Dict[str, Any] = {
    'temperature': 0.7,
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 1024,  # Reduced from 2048 to prevent timeouts
}

# Advanced configuration for the pipeline
ADVANCED_CONFIG: Dict[str, Any] = {
    'solution_temperature': 0.7,
    'critique_temperature': 0.6,
    'early_stopping_threshold': 0.85,
    'improvement_emphasis': 'balanced',
    'critique_depth': 'thorough',
    'max_retries': 3,
    'initial_delay': 1.0,
    'backoff_factor': 2.0
}

# Validate configurations
if not 0 <= GENERATION_CONFIG['temperature'] <= 1:
    raise ValueError("Temperature must be between 0 and 1")

if not 0 <= ADVANCED_CONFIG['early_stopping_threshold'] <= 1:
    raise ValueError("early_stopping_threshold must be between 0 and 1")
