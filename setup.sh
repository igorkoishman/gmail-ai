#!/bin/bash

echo "🚀 Setting up Gmail AI Categorization project..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Set up Gmail API credentials:"
echo "   - Go to: https://console.cloud.google.com/"
echo "   - Enable Gmail API"
echo "   - Create OAuth credentials"
echo "   - Download and save as 'client_secret.json'"
echo ""
echo "3. Get Gemini API key:"
echo "   - Go to: https://makersuite.google.com/app/apikey"
echo "   - Set: export GEMINI_API_KEY='your-key'"
echo ""
echo "4. Run the script:"
echo "   python main.py"
