#!/bin/bash

# Lumara Startup Script
# This script starts the Lumara API server

echo "Starting Lumara API server..."
echo "Make sure you have set your GOOGLE_API_KEY environment variable or have it in a .env file"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "lumara_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv lumara_venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created successfully."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source lumara_venv/bin/activate

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is required but not installed."
    exit 1
fi

# Check if requirements are installed
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists and load it
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: No .env file found. Make sure GOOGLE_API_KEY is set in your environment."
fi

# Check if API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment."
    echo "You can get an API key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Start the API server
echo "Starting API server on http://localhost:5000"
python api.py
