#!/bin/bash

# Lumara AI Deployment Script
# This script sets up Lumara for production deployment
# No API key configuration needed - users provide their own

set -e

echo "🚀 Starting Lumara AI deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is required but not installed."
        exit 1
    fi
}

print_status "Checking dependencies..."
check_command python3
check_command pip3

# Create virtual environment if it doesn't exist
if [ ! -d "lumara_venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv lumara_venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source lumara_venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn

# Install Refinery dependencies
if [ -d "../Refinery" ]; then
    print_status "Installing Refinery dependencies..."
    pip install -r ../Refinery/requirements.txt
else
    print_warning "Refinery directory not found. Make sure it's in the correct location."
fi

# Create logs directory
mkdir -p logs

print_status "Deployment setup complete!"
echo ""
print_status "🎉 Lumara AI is ready for deployment!"
echo ""
echo "Lumara is designed to be stateless - users provide their own API keys."
echo "No server-side API key configuration is needed."
echo ""
echo "To start the application:"
echo "- Development: python api.py"
echo "- Production: gunicorn --config gunicorn.conf.py wsgi:app"
echo "- Docker: docker-compose up -d"
echo ""
echo "Users will enter their Google Gemini API keys through the web interface."
