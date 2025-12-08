#!/bin/bash
# LLM Council - Simple Setup Script
# This script sets up everything automatically

echo "=========================================="
echo "LLM Council - Simple Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file for API key..."
    cat > .env << 'EOF'
# OpenRouter API Key
# Get your key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your-api-key-here

# Optional: Firestore settings
USE_FIRESTORE=true
EOF
    echo "✓ Created .env file"
    echo ""
    echo "IMPORTANT: Edit .env and add your actual OpenRouter API key!"
    echo "Location: .env"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Setup complete! Next steps:"
echo ""
echo "1. Edit .env and add your OpenRouter API key"
echo "2. Run: python -m backend.main"
echo "   OR"
echo "2. Run: bash deploy.sh"
echo ""
echo "=========================================="
