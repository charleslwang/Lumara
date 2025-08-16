#!/bin/bash

# Render.com build script for Lumara AI
set -e

echo "🚀 Starting Lumara AI build..."

# Install main dependencies
echo "📦 Installing main dependencies..."
pip install -r requirements.txt

# Install Refinery dependencies if available
if [ -d "../Refinery" ]; then
    echo "📦 Installing Refinery dependencies..."
    if [ -f "../Refinery/requirements.txt" ]; then
        pip install -r ../Refinery/requirements.txt
    else
        echo "⚠️  Refinery requirements.txt not found, skipping..."
    fi
else
    echo "⚠️  Refinery directory not found at ../Refinery"
    echo "ℹ️  This is okay - the app will still work with the bundled Refinery code"
fi

echo "✅ Build completed successfully!"
