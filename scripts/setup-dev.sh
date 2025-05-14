#!/bin/bash
# Script to initialize the development environment with uv

echo "🚀 Initializing development environment for RAVEN API"

# Check if uv is installed
if ! command -v uv &> /dev/null
then
    echo "❌ uv is not installed. Installing..."
    pip install uv
fi

# Create virtual environment with uv
echo "🔧 Creating virtual environment with uv..."
uv venv

# Activate the virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -r requirements.txt

# Create .env file from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Don't forget to edit the .env file with your configurations"
fi

# Initialize the database
echo "🗄️  Initializing database..."
python -m app.db.init_db

echo "✨ Environment successfully initialized. Use 'source .venv/bin/activate' to activate the virtual environment."
echo "▶️  Run 'python run.py' to start the API."
