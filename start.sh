#!/bin/bash

echo "🚀 Starting ESGenerator - Memory Optimized..."

cd backend

# Memory optimization settings
export FLASK_ENV=production
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Port configuration
if [ -z "$PORT" ]; then
    export PORT=10000
fi

echo "📊 Memory Optimized Startup:"
echo "  Environment: $FLASK_ENV"
echo "  Port: $PORT"
echo "  Python Optimization: Enabled"

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ SECRET_KEY not set"
    exit 1
fi

if [ -z "$NVIDIA_API_KEY" ]; then
    echo "❌ NVIDIA_API_KEY not set"
    exit 1
fi

echo "✅ Environment variables configured"

# Test basic functionality
echo "🔍 Testing basic imports..."
python3 -c "
import sys
import gc
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    print('✅ PyMySQL OK')
    
    from flask import Flask
    print('✅ Flask OK')
    
    # Force cleanup
    gc.collect()
    print('✅ Memory cleanup OK')
    
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Basic functionality test failed"
    exit 1
fi

# Test database connection
echo "🔍 Testing database connection..."
python3 -c "
import os
import sys
import gc
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    
    from flask import Flask
    from models import db
    from config import get_config
    
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Clean database URL
    database_url = os.environ.get('DATABASE_URL')
    if 'ssl-mode=' in database_url:
        parts = database_url.split('?')
        if len(parts) > 1:
            base_url = parts[0]
            params = parts[1].split('&')
            cleaned_params = [p for p in params if not p.startswith('ssl-mode=')]
            database_url = base_url + ('?' + '&'.join(cleaned_params) if cleaned_params else '')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    db.init_app(app)
    
    with app.app_context():
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1 as test'))
        test_result = result.fetchone()
        if test_result[0] == 1:
            print('✅ Database connection successful')
        else:
            print('❌ Database test failed')
            sys.exit(1)
    
    # Cleanup
    gc.collect()
    
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection test failed"
    exit 1
fi

echo "✅ All tests passed - starting server..."

# Start with memory-optimized Gunicorn settings
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --worker-class sync \
    --worker-connections 100 \
    --timeout 300 \
    --keepalive 5 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level warning \
    --capture-output \
    app:app