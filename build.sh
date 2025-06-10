#!/bin/bash
# =============================================================================
# File: build.sh (Updated with model validation)
# =============================================================================
set -e

echo "🚀 Starting build process..."

# Build Frontend
echo "📦 Building Frontend..."
cd frontend

echo "  Installing npm dependencies..."
npm ci --production=false

echo "  Building React application..."
npm run build

echo "  ✅ Frontend build completed"

# Setup Backend
echo ""
echo "🐍 Setting up Backend..."
cd ../backend

echo "  Installing Python dependencies..."
pip install --upgrade pip

# Install PyMySQL first to ensure MySQLdb compatibility
echo "  📚 Installing PyMySQL for MySQL compatibility..."
pip install PyMySQL==1.1.0

# Install other requirements
pip install -r requirements.txt

# Download NLTK data
echo "  📚 Downloading NLTK data..."
python3 -c "
import nltk
import ssl

print('Downloading NLTK punkt tokenizer...')

# Handle SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.download('punkt', quiet=True)
    print('✅ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠️ NLTK download warning: {e}')
"

# Test model definitions
echo "  🧪 Testing model definitions..."
python3 test_models.py
if [ $? -ne 0 ]; then
    echo "❌ Model validation failed"
    exit 1
fi

# Verify vectorstores exist
echo "  🔍 Checking vectorstores..."
if [ -d "vectorstores" ]; then
    echo "  ✅ Vectorstores directory found"
    
    # Check for required directories
    required_dirs=("nace_db" "default_db" "oil_gas_db" "mining_db" "road_db")
    for dir in "${required_dirs[@]}"; do
        if [ -d "vectorstores/$dir" ]; then
            echo "    ✅ $dir found"
        else
            echo "    ⚠️ $dir not found"
        fi
    done
else
    echo "  ❌ Vectorstores directory not found!"
    echo "  Make sure vectorstores/ folder is in your repository"
    exit 1
fi

# Initialize database with improved debugging
echo "  🗄️ Initializing database..."
python3 debug_init_db.py

echo ""
echo "✅ Build process completed successfully!"