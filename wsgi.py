#!/usr/bin/env python3
"""
WSGI entry point for Lumara application.
This file is used by production WSGI servers like Gunicorn.

Lumara is designed to be stateless - users provide their own API keys,
so no environment configuration is needed.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the Flask app
from api import app

# Set production environment variables
os.environ.setdefault('FLASK_ENV', 'production')

if __name__ == "__main__":
    app.run()
