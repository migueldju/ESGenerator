from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import json
import re
import warnings
import faiss
import pickle
import markdown
import uuid
import jwt
from functools import wraps
from langchain.chains import RetrievalQA
from sentence_transformers import CrossEncoder
from openai import OpenAI
from langchain_core.runnables import Runnable

# Import the db instance and models from models.py
from models import db, User, Conversation, Answer, Document

# Initialize Flask app
app = Flask(__name__, static_folder='./build', template_folder='./build')
app.config['SECRET_KEY'] = 'esrs_generator_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///esrs_db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Change to your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')
app.config['MAIL_SUPPRESS_SEND'] = True  # Set to False in production with valid credentials'

# JWT configuration
app.config['JWT_SECRET_KEY'] = 'esrs_jwt_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
db.init_app(app)  # Initialize db with app
bcrypt = Bcrypt(app)
mail = Mail(app)

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})

# Explicitly set session cookie parameters
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Or 'None' with secure=True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Create database tables
with app.app_context():
    db.create_all()

# Helper functions for sending emails
def send_verification_email(user):
    token = str(uuid.uuid4())
    user.verification_token = token
    db.session.commit()
    
    verification_url = f"http://localhost:5173/verify/{token}"
    
    msg = Message(
        subject="ESGenerator - Verify Your Email",
        recipients=[user.email],
        html=f"""
        <h1>Welcome to ESGenerator!</h1>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>If you didn't register for an account, please ignore this email.</p>
        """
    )
    mail.send(msg)

def send_password_reset_email(user):
    token = str(uuid.uuid4())
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    reset_url = f"http://localhost:5173/reset-password/{token}"
    
    msg = Message(
        subject="ESGenerator - Reset Your Password",
        recipients=[user.email],
        html=f"""
        <h1>Password Reset Request</h1>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request a password reset, please ignore this email.</p>
        """
    )
    mail.send(msg)

# Middleware to verify JWT token
def token_required(f):
    @wraps(f)  # This preserves the original function name and metadata
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token or not token.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid token"}), 401
        
        token = token.split('Bearer ')[1]
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({"error": "Invalid or expired token"}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 409
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    new_user = User(
        username=username,
        email=email,
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # In development mode, auto-verify the user without email
    if app.config['MAIL_SUPPRESS_SEND']:
        new_user.is_verified = True
        db.session.commit()
        return jsonify({"message": "Registration successful. Email verification skipped in development mode."}), 201
    
    # Try to send verification email
    try:
        send_verification_email(new_user)
        return jsonify({"message": "Registration successful. Please check your email to verify your account."}), 201
    except Exception as e:
        app.logger.error(f"Failed to send verification email: {str(e)}")
        # Still return success since user is created, but with a warning
        return jsonify({"message": "Registration successful, but email verification could not be sent. Please contact support."}), 201

@app.route('/api/verify/<token>', methods=['GET'])
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return jsonify({"error": "Invalid verification token"}), 400
    
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    
    return redirect('http://localhost:5173/login?verified=true')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    if not user.is_verified:
        return jsonify({"error": "Please verify your email before logging in"}), 401
    
    # Generate JWT token
    access_token = jwt.encode(
        {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        },
        app.config['JWT_SECRET_KEY']
    )
    
    return jsonify({
        "token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # For security reasons, don't reveal that the email doesn't exist
        return jsonify({"message": "If your email exists in our system, you will receive a password reset link"}), 200
    
    try:
        send_password_reset_email(user)
        return jsonify({"message": "Reset link sent to your email"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send reset email: {str(e)}"}), 500

@app.route('/api/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({"error": "Password is required"}), 400
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expiry < datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400
    
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()
    
    return jsonify({"message": "Password reset successful"}), 200

# Conversation routes
@app.route('/api/conversations', methods=['GET'])
@token_required
def get_conversations(current_user):
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    
    conversations_list = []
    for conv in conversations:
        conversations_list.append({
            'id': conv.id,
            'title': conv.title,
            'nace_sector': conv.nace_sector,
            'esrs_sector': conv.esrs_sector,
            'created_at': conv.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': conv.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({"conversations": conversations_list}), 200

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@token_required
def get_conversation(current_user, conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    answers = Answer.query.filter_by(conversation_id=conversation_id).order_by(Answer.created_at).all()
    
    answers_list = []
    for answer in answers:
        answers_list.append({
            'id': answer.id,
            'question': answer.question,
            'answer': answer.answer,
            'created_at': answer.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        "conversation": {
            'id': conversation.id,
            'title': conversation.title,
            'nace_sector': conversation.nace_sector,
            'esrs_sector': conversation.esrs_sector,
            'company_description': conversation.company_description,
            'created_at': conversation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        },
        "answers": answers_list
    }), 200

# Document routes
@app.route('/api/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.updated_at.desc()).all()
    
    documents_list = []
    for doc in documents:
        documents_list.append({
            'id': doc.id,
            'name': doc.name,
            'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': doc.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({"documents": documents_list}), 200

@app.route('/api/documents/<int:document_id>', methods=['GET'])
@token_required
def get_document(current_user, document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify({
        "document": {
            'id': document.id,
            'name': document.name,
            'content': document.content,
            'created_at': document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': document.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200

@app.route('/api/documents', methods=['POST'])
@token_required
def create_document(current_user):
    data = request.get_json()
    
    name = data.get('name')
    content = data.get('content')
    
    if not name or not content:
        return jsonify({"error": "Name and content are required"}), 400
    
    document = Document(
        user_id=current_user.id,
        name=name,
        content=content
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        "message": "Document created successfully",
        "document": {
            'id': document.id,
            'name': document.name,
            'created_at': document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': document.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201

@app.route('/api/documents/<int:document_id>', methods=['PUT'])
@token_required
def update_document(current_user, document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        document.name = data['name']
    
    if 'content' in data:
        document.content = data['content']
    
    db.session.commit()
    
    return jsonify({
        "message": "Document updated successfully",
        "document": {
            'id': document.id,
            'name': document.name,
            'created_at': document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': document.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200

@app.route('/api/documents/<int:document_id>', methods=['DELETE'])
@token_required
def delete_document(current_user, document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    db.session.delete(document)
    db.session.commit()
    
    return jsonify({"message": "Document deleted successfully"}), 200

# Existing code for LLM and vectorstore handling
warnings.filterwarnings("ignore")

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key="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"
)

def load_vectorstore(db_folder):
    db_path = os.path.join("vectorstores", db_folder)

    index = faiss.read_index(os.path.join(db_path, "index.faiss"))

    with open(os.path.join(db_path, "vectorstore.pkl"), "rb") as f:
        vectorstore = pickle.load(f)

    vectorstore.index = index
    return vectorstore

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

def get_llm_response(prompt):
    completion = client.chat.completions.create(
        model="nvidia/llama-3.3-nemotron-super-49b-v1",
        messages=[{"role": "system", "content": "Be brief."
        "Only return the most COMPLETE and accurate answer. "
        "Avoid explanations, introductions, and additional context. "
        "No need to introduce a summary at the end. "},
                  {"role": "user", "content": prompt}],
        temperature=0,
        top_p=0.1,
        max_tokens=112000,
        frequency_penalty=0.1,
        presence_penalty=0,
        stream=False
    )
    return completion.choices[0].message.content.strip()

class NvidiaLLM(Runnable):
    def invoke(self, input):
        return get_llm_response(input["query"])

def load_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10})
    return RetrievalQA.from_chain_type(
        llm=NvidiaLLM(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

nace_vs = load_vectorstore("nace_db")
default_vs = load_vectorstore("default_db")

sector_vectorstores = {}
merged_vectorstores = {}

sector_db_map = {
    "Oil & Gas Company": "oil_gas_db",
    "Mining, Quarrying and Coal": "mining_db",
    "Road Transport": "road_db"
}

for sector, db_name in sector_db_map.items():
    sector_vectorstores[sector] = load_vectorstore(db_name)

    sector_vs = sector_vectorstores[sector]

    default_docs = default_vs.similarity_search("", k=100000)  
    
    sector_docs = sector_vs.similarity_search("", k=100000) 
    
    all_docs = default_docs + sector_docs
    
    merged_vectorstores[sector] = {
        'vectorstore': sector_vs,
        'docs': all_docs
    }

with open("sector_classification.json", "r", encoding="utf-8") as f:
    special_sectors = json.load(f)

nace_chain = load_chain(nace_vs)

# Modified chat endpoint to support user sessions and conversation history
@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    data = request.get_json()
    user_message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    if conversation_id:
        # Existing conversation
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        
        company_desc = conversation.company_description
        nace_sector = conversation.nace_sector
        esrs_sector = conversation.esrs_sector
        
        # Get conversation history
        answers = Answer.query.filter_by(conversation_id=conversation_id).order_by(Answer.created_at).all()
        conversation_history = []
        
        for answer in answers:
            conversation_history.append(f"Q: {answer.question}")
            conversation_history.append(f"A: {answer.answer}")
        
        # Process the question
        qa_vs = default_vs
        
        if esrs_sector in sector_db_map:
            merged_data = merged_vectorstores.get(esrs_sector)
            
            if merged_data:
                qa_vs = merged_data['vectorstore']
        
        retrieved_docs = qa_vs.similarity_search(user_message, k=10)
        
        ranked_docs = sorted(
            retrieved_docs,
            key=lambda doc: reranker.predict([(user_message, doc.page_content)]),
            reverse=True
        )[:5]
        
        context = "\n".join([doc.page_content for doc in ranked_docs])
        
        contextual_query = f"""
        Instructions:
        - Follow the ESRS standards.
        - Use the context provided for reference.
        - No need to include summary tables
        - Answer must be complete and accurate
        - Give brief and concise answers
        - Prioritize information quality over aesthetics
        - Don't show tables, only plain text
        - Don't say what was provided in context
        - Give answer in markdown format
        - Don't include numeric lists, only bullet points
        Question: {user_message}
        Context:
        {context}
        Take into account the previous conversation:
        {conversation_history}
        """
        
        answer_text = get_llm_response(contextual_query)
        answer_html = markdown.markdown(answer_text, extensions=['tables', 'md_in_html'])
        
        # Store the question and answer in the database
        answer = Answer(
            conversation_id=conversation_id,
            question=user_message,
            answer=answer_html
        )
        
        db.session.add(answer)
        db.session.commit()
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'answer': answer_html,
            'context': context,
            'is_first_message': False
        }), 200
    else:
        # New conversation
        company_desc = user_message
        result = process_company_description(company_desc)
        
        # Generate title using LLM
        title_prompt = f"""
        Generate a short title (max 6 words) for a conversation about ESRS reporting requirements based on this company description:
        {company_desc}
        Just return the title without any quotation marks or additional text.
        """
        conversation_title = get_llm_response(title_prompt)
        
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            nace_sector=result['nace_sector'],
            title=conversation_title,
            esrs_sector=result['esrs_sector'],
            company_description=company_desc
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        welcome_answer = f"Thank you for your company description. Based on my analysis, your company falls under NACE sector {result['nace_sector']}. How can I help you with your ESRS reporting requirements?"
        
        # Create initial answer
        answer = Answer(
            conversation_id=conversation.id,
            question=company_desc,
            answer=welcome_answer
        )
        
        db.session.add(answer)
        db.session.commit()
        
        return jsonify({
            'answer': welcome_answer,
            'context': '',
            'is_first_message': True,
            'conversation_id': conversation.id,
            'nace_sector': result['nace_sector'],
            'esrs_sector': result['esrs_sector']
        }), 200

def process_company_description(company_desc):
    retrieved_docs = nace_vs.similarity_search(company_desc, k=3)
    
    ranked_docs = sorted(
        retrieved_docs,
        key=lambda doc: reranker.predict([(company_desc, doc.page_content)]),
        reverse=True
    )[:3]
    
    context = "\n".join([doc.page_content for doc in ranked_docs])
    
    contextual_query = f"""
    You are a NACE classification assistant.
    Your job is to identify and return the exact NACE code.

    Instructions:
    - Analyze the company description.
    - Use the context provided for reference.
    - Respond with ONLY the NACE code (e.g., 'A01.1' or 'B05').
    - Don't forget to include the letter

    Company description:
    {company_desc}

    Context:
    {context}
    """
    
    nace_result = get_llm_response(contextual_query)
    
    nace_result = re.sub(r'(\b[a-u]\b)', lambda m: m.group(1).upper(), nace_result)
    nace_result = re.sub(r'\.\s+', '.', nace_result)
    
    match = re.search(r'([A-U](\d{1,2})(\.\d{1,2}){0,2})', nace_result)
    
    if match:
        nace_sector = match.group(1)
        print(f"Company sector according to NACE: {nace_sector}") 
        esrs_sector = special_sectors.get(nace_sector, "Agnostic")
    else:
        nace_sector = "Agnostic"
        print("Could not determine exact NACE code. Using agnostic standards.") 
        esrs_sector = "Agnostic"
    
    return {
        'nace_sector': nace_sector,
        'esrs_sector': esrs_sector
    }

@app.route('/api/reset', methods=['POST'])
@token_required
def reset_session(current_user):
    return jsonify({'status': 'success'})

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.template_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)