#!/bin/bash

# Gmail AI Categorization - Easy run script
# Automatically loads environment variables and runs the application

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Gmail AI Categorization${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Run: ./setup.sh first"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Create .env file with GEMINI_API_KEY"
    exit 1
fi

# Check credentials
echo -e "${GREEN}🔍 Checking configuration...${NC}"
python config.py
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Configuration check failed!${NC}"
    exit 1
fi

# Check if Gmail token exists, if not run setup
if [ ! -f "token.json" ]; then
    echo ""
    echo -e "${BLUE}🔐 Gmail authentication required...${NC}"
    python setup_credentials.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Authentication failed!${NC}"
        exit 1
    fi
fi

# Run main script with any additional arguments
echo ""
echo -e "${GREEN}▶️  Running Gmail AI categorization...${NC}"
echo ""
python main.py "$@"

echo ""
echo -e "${GREEN}✅ Done!${NC}"
