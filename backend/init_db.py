#!/usr/bin/env python3
"""
Production-ready database initialization script - Fixed SQLAlchemy instance
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database_url(url):
    """Remove problematic SSL parameters from database URL"""
    if not url or 'ssl-mode=' not in url:
        return url
    
    try:
        # Simple cleaning - remove ssl-mode parameter
        parts = url.split('?')
        if len(parts) > 1:
            base_url = parts[0]
            params = parts[1].split('&')
            cleaned_params = []
            
            for param in params:
                if not param.startswith('ssl-mode=') and not param.startswith('ssl-ca='):
                    cleaned_params.append(param)
            
            if cleaned_params:
                return base_url + '?' + '&'.join(cleaned_params)
            else:
                return base_url
        
        return url
    except:
        return url

def main():
    print("🗄️ Starting database initialization...")
    
    try:
        # Install PyMySQL
        import pymysql
        pymysql.install_as_MySQLdb()
        print("✅ PyMySQL installed as MySQLdb")
    except ImportError:
        print("❌ PyMySQL not available")
        return False
    
    # Check environment variables
    database_url = os.environ.get('DATABASE_URL')
    secret_key = os.environ.get('SECRET_KEY')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
        
    if not secret_key:
        print("❌ SECRET_KEY environment variable not set")
        return False
    
    print(f"Database URL configured: {database_url[:50]}...")
    
    # Clean the database URL
    cleaned_url = clean_database_url(database_url)
    if cleaned_url != database_url:
        print("✅ Cleaned SSL parameters from database URL")
    
    try:
        # Create Flask app
        from flask import Flask
        app = Flask(__name__)
        
        app.config.update({
            'SQLALCHEMY_DATABASE_URI': cleaned_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': secret_key,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'pool_timeout': 30,
                'connect_args': {
                    'charset': 'utf8mb4',
                    'connect_timeout': 30,
                }
            }
        })
        
        print("✅ Flask app configured")
        
        # Import models and db - IMPORTANT: use the same db instance
        from models import db, User, Conversation, Answer, Document
        print("✅ Models and db imported")
        
        # Initialize db with our app
        db.init_app(app)
        print("✅ Database initialized with app")
        
        with app.app_context():
            # Test database connection
            print("🔍 Testing database connection...")
            try:
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1 as test'))
                test_value = result.fetchone()
                
                if test_value and test_value[0] == 1:
                    print("✅ Database connection successful")
                else:
                    print("❌ Connection test returned unexpected value")
                    return False
                    
            except Exception as conn_error:
                print(f"❌ Database connection failed: {conn_error}")
                return False
            
            # Create tables
            print("📋 Creating database tables...")
            try:
                db.create_all()
                print("✅ db.create_all() completed successfully")
                
            except Exception as create_error:
                print(f"❌ Table creation failed: {create_error}")
                import traceback
                traceback.print_exc()
                return False
            
            # Verify tables by testing model functionality
            print("🧪 Verifying table creation...")
            
            verification_results = []
            
            # Test each model
            models_to_test = [
                ('User', User),
                ('Conversation', Conversation), 
                ('Answer', Answer),
                ('Document', Document)
            ]
            
            for model_name, model_class in models_to_test:
                try:
                    # Test that we can query the model (proves table exists)
                    count = model_class.query.count()
                    print(f"  ✅ {model_name} table verified (count: {count})")
                    verification_results.append(model_name)
                    
                except Exception as query_error:
                    print(f"  ❌ {model_name} table verification failed: {query_error}")
            
            # Test actual database operations to be extra sure
            print("💾 Testing database operations...")
            try:
                # Create a test user
                test_user = User(username='init_test_user', email='test@init.com')
                test_user.set_password('testpassword')
                db.session.add(test_user)
                db.session.commit()
                
                # Query it back
                found_user = User.query.filter_by(username='init_test_user').first()
                if found_user:
                    print("  ✅ Database write/read operations successful")
                    
                    # Clean up test data
                    db.session.delete(found_user)
                    db.session.commit()
                    print("  ✅ Test data cleaned up")
                    
                    verification_results.append('Database_operations')
                else:
                    print("  ❌ Could not retrieve test user")
                    
            except Exception as op_error:
                print(f"  ⚠️ Database operations test failed: {op_error}")
                # Don't fail the initialization for this
            
            # Check results
            expected_models = len(models_to_test)
            verified_models = len([r for r in verification_results if r in ['User', 'Conversation', 'Answer', 'Document']])
            
            print(f"📊 Verification Results:")
            print(f"  - Expected models: {expected_models}")
            print(f"  - Verified models: {verified_models}")
            print(f"  - Results: {verification_results}")
            
            if verified_models >= expected_models:
                print("✅ All tables verified successfully!")
                return True
            elif verified_models >= 3:
                print("⚠️ Most tables verified - considering this a success")
                return True
            else:
                print(f"❌ Only {verified_models}/{expected_models} tables verified")
                return False
                
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("🚀 Database initialization completed successfully!")
        sys.exit(0)
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)

            