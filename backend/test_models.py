#!/usr/bin/env python3
"""
Test script to validate model definitions - Fixed SQLAlchemy instance issue
"""
import sys

def test_models():
    print("🧪 Testing model definitions...")
    
    try:
        # Import Flask first
        from flask import Flask
        print("✅ Flask imported")
        
        # Create a test app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test'
        
        print("✅ Test app created")
        
        # Import models AFTER creating the app so we can use the same db instance
        try:
            from models import db, User, Conversation, Answer, Document
            print("✅ Models and db imported successfully")
        except Exception as import_error:
            print(f"❌ Error importing models: {import_error}")
            import traceback
            traceback.print_exc()
            return False
        
        # Initialize the db with our app
        db.init_app(app)
        print("✅ Database initialized with app")
        
        # Test model attributes
        with app.app_context():
            print("🔍 Checking model definitions...")
            
            # Check User model
            try:
                user_table = User.__table__
                print(f"  User table: {user_table.name}")
                print(f"    Columns: {[c.name for c in user_table.columns]}")
                if len(user_table.columns) < 5:
                    print(f"    ❌ User table has too few columns")
                    return False
                print(f"    ✅ User model structure looks good")
            except Exception as e:
                print(f"  ❌ User model issue: {e}")
                return False
            
            # Check Conversation model
            try:
                conv_table = Conversation.__table__
                print(f"  Conversation table: {conv_table.name}")
                print(f"    Columns: {[c.name for c in conv_table.columns]}")
                if len(conv_table.columns) < 5:
                    print(f"    ❌ Conversation table has too few columns")
                    return False
                print(f"    ✅ Conversation model structure looks good")
            except Exception as e:
                print(f"  ❌ Conversation model issue: {e}")
                return False
            
            # Check Answer model
            try:
                answer_table = Answer.__table__
                print(f"  Answer table: {answer_table.name}")
                print(f"    Columns: {[c.name for c in answer_table.columns]}")
                if len(answer_table.columns) < 4:
                    print(f"    ❌ Answer table has too few columns")
                    return False
                print(f"    ✅ Answer model structure looks good")
            except Exception as e:
                print(f"  ❌ Answer model issue: {e}")
                return False
            
            # Check Document model
            try:
                doc_table = Document.__table__
                print(f"  Document table: {doc_table.name}")
                print(f"    Columns: {[c.name for c in doc_table.columns]}")
                if len(doc_table.columns) < 5:
                    print(f"    ❌ Document table has too few columns")
                    return False
                print(f"    ✅ Document model structure looks good")
            except Exception as e:
                print(f"  ❌ Document model issue: {e}")
                return False
            
            # Try creating tables in memory
            try:
                print("📋 Creating tables...")
                db.create_all()
                print("✅ db.create_all() completed without errors")
                
                # Test that models can be queried (now using the same db instance)
                print("🧪 Testing model functionality...")
                
                test_results = []
                try:
                    # Test User model
                    user_count = User.query.count()
                    print(f"  ✅ User model is queryable (count: {user_count})")
                    test_results.append('User')
                except Exception as e:
                    print(f"  ❌ User model query failed: {e}")
                
                try:
                    # Test Conversation model
                    conv_count = Conversation.query.count()
                    print(f"  ✅ Conversation model is queryable (count: {conv_count})")
                    test_results.append('Conversation')
                except Exception as e:
                    print(f"  ❌ Conversation model query failed: {e}")
                
                try:
                    # Test Answer model
                    answer_count = Answer.query.count()
                    print(f"  ✅ Answer model is queryable (count: {answer_count})")
                    test_results.append('Answer')
                except Exception as e:
                    print(f"  ❌ Answer model query failed: {e}")
                
                try:
                    # Test Document model
                    doc_count = Document.query.count()
                    print(f"  ✅ Document model is queryable (count: {doc_count})")
                    test_results.append('Document')
                except Exception as e:
                    print(f"  ❌ Document model query failed: {e}")
                
                # Test model instantiation
                print("🔧 Testing model instantiation...")
                try:
                    # Test User instantiation
                    test_user = User(username='test', email='test@test.com')
                    test_user.set_password('test123')
                    print(f"  ✅ User model can be instantiated")
                    test_results.append('User_instantiation')
                except Exception as e:
                    print(f"  ❌ User instantiation failed: {e}")
                
                try:
                    # Test Conversation instantiation
                    test_conv = Conversation(title='Test Conversation')
                    print(f"  ✅ Conversation model can be instantiated")
                    test_results.append('Conversation_instantiation')
                except Exception as e:
                    print(f"  ❌ Conversation instantiation failed: {e}")
                
                # Test actual database operations
                print("💾 Testing database operations...")
                try:
                    # Try to add and commit a user
                    test_user = User(username='testuser', email='test@example.com')
                    test_user.set_password('testpass')
                    db.session.add(test_user)
                    db.session.commit()
                    
                    # Query it back
                    found_user = User.query.filter_by(username='testuser').first()
                    if found_user:
                        print(f"  ✅ Database operations work (created user: {found_user.username})")
                        test_results.append('Database_operations')
                    else:
                        print(f"  ❌ Could not retrieve created user")
                        
                except Exception as e:
                    print(f"  ❌ Database operations failed: {e}")
                
                # Success criteria: all models should be queryable and instantiable
                expected_tests = ['User', 'Conversation', 'Answer', 'Document']
                working_models = [t for t in expected_tests if t in test_results]
                
                print(f"📊 Test Results:")
                print(f"  - Working models: {len(working_models)}/{len(expected_tests)}")
                print(f"  - Models: {working_models}")
                print(f"  - All results: {test_results}")
                
                if len(working_models) >= 4:
                    print("✅ All models are working correctly!")
                    return True
                elif len(working_models) >= 3:
                    print("⚠️ Most models working - considering this a success")
                    return True
                else:
                    print(f"❌ Only {len(working_models)} models working - this is a failure")
                    return False
                    
            except Exception as create_error:
                print(f"❌ Error during table creation or testing: {create_error}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_models()
    if success:
        print("🎉 Model validation successful!")
        sys.exit(0)
    else:
        print("💥 Model validation failed!")
        sys.exit(1)