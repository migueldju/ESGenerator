from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import uuid

# Initialize db object that will be imported by other modules
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('Document', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Set password hash"""
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password, password)
    
    def generate_token(self):
        """Generate a unique token"""
        return str(uuid.uuid4())
    
    def __repr__(self):
        return f'<User {self.username}>'

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    nace_sector = db.Column(db.String(20), nullable=True)
    title = db.Column(db.Text, nullable=False)
    esrs_sector = db.Column(db.String(50), nullable=True)
    company_description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    answers = db.relationship('Answer', backref='conversation', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.title[:50]}>'

class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Answer {self.id} for Conversation {self.conversation_id}>'

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Document {self.id}: {self.name}>'

# Create indexes for better performance
def create_indexes(db_instance):
    """Create additional indexes for better performance"""
    try:
        # These will be created automatically due to the index=True parameters above
        # But we can add custom indexes here if needed
        pass
    except Exception as e:
        print(f"Warning: Could not create additional indexes: {e}")

# Validation functions
def validate_models():
    """Validate that all models are properly defined"""
    models = [User, Conversation, Answer, Document]
    
    for model in models:
        if not hasattr(model, '__tablename__'):
            raise ValueError(f"Model {model.__name__} missing __tablename__")
        
        if not hasattr(model, '__table__'):
            raise ValueError(f"Model {model.__name__} missing __table__")
    
    return True