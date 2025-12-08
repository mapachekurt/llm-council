#!/bin/bash

# LLM Council - Deployment Script
# Deploys the CTO Council to Google Cloud Firebase

set -e

echo "=========================================="
echo "LLM Council - Google Cloud Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v firebase &> /dev/null; then
    echo -e "${RED}Error: Firebase CLI is not installed${NC}"
    echo "Install it with: npm install -g firebase-tools"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Check if Firebase project is configured
echo -e "${YELLOW}Checking Firebase configuration...${NC}"

if [ ! -f ".firebaserc" ]; then
    echo -e "${RED}Error: .firebaserc not found${NC}"
    echo "Run 'firebase init' to configure your Firebase project"
    exit 1
fi

PROJECT_ID=$(grep -o '"projects":[^}]*' .firebaserc | grep -o '"default":"[^"]*' | grep -o '[^"]*$')
echo -e "${GREEN}✓ Firebase project configured: ${PROJECT_ID}${NC}"
echo ""

# Set environment variables
echo -e "${YELLOW}Setting up environment...${NC}"

# Check for OPENROUTER_API_KEY
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}Error: OPENROUTER_API_KEY environment variable not set${NC}"
    echo "Set it with: export OPENROUTER_API_KEY='your-api-key'"
    exit 1
fi

echo -e "${GREEN}✓ OPENROUTER_API_KEY is set${NC}"
echo ""

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}Error: Frontend build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend built successfully${NC}"
cd ..
echo ""

# Install backend dependencies
echo -e "${YELLOW}Checking backend dependencies...${NC}"

if [ ! -d "functions/.venv" ]; then
    echo "Creating Python virtual environment..."
    cd functions
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
fi

echo -e "${GREEN}✓ Backend dependencies ready${NC}"
echo ""

# Set Firebase secrets
echo -e "${YELLOW}Setting up Firebase secrets...${NC}"

firebase functions:secrets:set OPENROUTER_API_KEY --project="${PROJECT_ID}"

echo -e "${GREEN}✓ Secrets configured${NC}"
echo ""

# Deploy to Firebase
echo -e "${YELLOW}Deploying to Firebase...${NC}"
echo "This may take a few minutes..."
echo ""

firebase deploy --project="${PROJECT_ID}"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✓ Deployment successful!"
    echo "==========================================${NC}"
    echo ""
    echo "Your LLM Council is now live:"
    echo "  Project: ${PROJECT_ID}"
    echo ""
    echo "Next steps:"
    echo "  1. Visit your Firebase Hosting URL"
    echo "  2. Start a new conversation to test"
    echo "  3. Monitor logs: firebase functions:log --project=${PROJECT_ID}"
    echo ""
else
    echo -e "${RED}Deployment failed. Check the errors above.${NC}"
    exit 1
fi
