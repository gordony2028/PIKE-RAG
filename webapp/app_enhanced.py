#!/usr/bin/env python3
"""
PIKE-RAG Enhanced Web Application
Built with Flask and integrated with Azure OpenAI
Features: Document Upload, Multi-turn Conversations, Advanced Reasoning, Custom Knowledge Bases
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pikerag.utils.config_loader import load_dot_env
from pikerag.llm_client.azure_open_ai_client import AzureOpenAIClient
from pikerag.utils.logger import Logger

# Import our new modules
from document_processor import DocumentProcessor
from conversation_manager import ConversationManager
from reasoning_strategies import ReasoningStrategyManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
KNOWLEDGE_BASE_FOLDER = os.path.join(os.path.dirname(__file__), 'knowledge_base')
SESSIONS_FOLDER = os.path.join(os.path.dirname(__file__), 'sessions')

# Global variables for PIKE-RAG components
client = None
logger = None
doc_processor = None
conversation_manager = None
reasoning_manager = None

def initialize_pikerag():
    """Initialize PIKE-RAG components"""
    global client, logger, doc_processor, conversation_manager, reasoning_manager
    
    try:
        # Load environment variables
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env_configs', '.env')
        load_dot_env(env_path)
        
        # Create logger
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logger = Logger(name='webapp_enhanced', dump_folder=log_dir, dump_mode='a')
        
        # Initialize Azure OpenAI client
        cache_path = os.path.join(log_dir, 'webapp_enhanced_cache.db')
        client = AzureOpenAIClient(
            location=cache_path,
            auto_dump=True,
            logger=logger
        )
        
        # Initialize advanced components
        doc_processor = DocumentProcessor(UPLOAD_FOLDER, KNOWLEDGE_BASE_FOLDER)
        conversation_manager = ConversationManager(SESSIONS_FOLDER)
        reasoning_manager = ReasoningStrategyManager()
        
        print("✅ All PIKE-RAG enhanced components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize PIKE-RAG enhanced components: {e}")
        return False

@app.route('/')
def index():
    """Enhanced main page"""
    return render_template('index_enhanced.html')

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Enhanced API endpoint for asking questions with advanced features"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        session_id = data.get('session_id')
        reasoning_strategy = data.get('reasoning_strategy', 'generation')
        knowledge_base = data.get('knowledge_base', 'documents')
        use_retrieval = data.get('use_retrieval', True)
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        start_time = time.time()
        
        # Get or create session
        if not session_id:
            session_id = conversation_manager.create_session(reasoning_strategy, knowledge_base)
        
        # Get conversation history
        conversation_history = []
        if session_id:
            history_messages = conversation_manager.get_context_for_llm(session_id, include_summary=True)
            conversation_history = history_messages
        
        # Retrieve relevant context if enabled
        context = []
        if use_retrieval:
            try:
                search_results = doc_processor.search_knowledge_base(question, knowledge_base, n_results=5)
                context = [result['content'] for result in search_results]
            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")
                context = []
        
        # LLM configuration
        llm_config = {
            'model': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 800
        }
        
        # Process question using selected reasoning strategy
        result = reasoning_manager.process_with_strategy(
            strategy_name=reasoning_strategy,
            question=question,
            context=context,
            conversation_history=conversation_history,
            llm_client=client,
            llm_config=llm_config
        )
        
        processing_time = time.time() - start_time
        
        # Save conversation
        if session_id:
            conversation_manager.add_message(session_id, 'user', question)
            if result.get('success'):
                conversation_manager.add_message(session_id, 'assistant', result['answer'], {
                    'reasoning_strategy': reasoning_strategy,
                    'context_used': len(context),
                    'processing_time': processing_time
                })
        
        # Prepare enhanced response
        response_data = {
            'success': result.get('success', False),
            'question': question,
            'answer': result.get('answer', 'No answer generated'),
            'rationale': result.get('rationale', ''),
            'reasoning_strategy': reasoning_strategy,
            'reasoning_steps': result.get('reasoning_steps', []),
            'session_id': session_id,
            'knowledge_base': knowledge_base,
            'context_used': len(context),
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat(),
            'model': llm_config['model']
        }
        
        if not result.get('success'):
            response_data['error'] = result.get('error', 'Unknown error')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing enhanced question: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'question': data.get('question', '') if 'data' in locals() else ''
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """API endpoint for document upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        collection_name = request.form.get('collection_name', 'documents')
        
        # Validate file type
        allowed_extensions = {'pdf', 'docx', 'doc', 'txt'}
        file_extension = file.filename.lower().split('.')[-1]
        
        if file_extension not in allowed_extensions:
            return jsonify({
                'error': f'Unsupported file type: {file_extension}',
                'allowed_types': list(allowed_extensions)
            }), 400
        
        # Process the document
        result = doc_processor.process_uploaded_file(file, collection_name)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/knowledge-bases', methods=['GET'])
def list_knowledge_bases():
    """API endpoint to list knowledge bases (collections)"""
    try:
        collections = doc_processor.get_collections()
        return jsonify({
            'success': True,
            'knowledge_bases': collections
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/knowledge-bases/<collection_name>/files', methods=['GET'])
def list_knowledge_base_files(collection_name):
    """API endpoint to list files in a knowledge base"""
    try:
        files = doc_processor.get_file_info(collection_name)
        return jsonify({
            'success': True,
            'collection_name': collection_name,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/knowledge-bases/<collection_name>', methods=['DELETE'])
def delete_knowledge_base(collection_name):
    """API endpoint to delete a knowledge base"""
    try:
        result = doc_processor.delete_collection(collection_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """API endpoint to list conversation sessions"""
    try:
        sessions = conversation_manager.list_sessions()
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """API endpoint to create a new conversation session"""
    try:
        data = request.get_json() or {}
        reasoning_strategy = data.get('reasoning_strategy', 'generation')
        knowledge_base = data.get('knowledge_base', 'documents')
        
        session_id = conversation_manager.create_session(reasoning_strategy, knowledge_base)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'reasoning_strategy': reasoning_strategy,
            'knowledge_base': knowledge_base
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """API endpoint to get session details"""
    try:
        session = conversation_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'success': True,
            'session': session.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """API endpoint to delete a conversation session"""
    try:
        success = conversation_manager.delete_session(session_id)
        if success:
            return jsonify({'success': True, 'message': 'Session deleted'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete session'}), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """API endpoint to get conversation history"""
    try:
        limit = request.args.get('limit', 20, type=int)
        messages = conversation_manager.get_conversation_history(session_id, limit)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'messages': [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reasoning-strategies', methods=['GET'])
def list_reasoning_strategies():
    """API endpoint to list available reasoning strategies"""
    try:
        strategies = reasoning_manager.list_strategies()
        return jsonify({
            'success': True,
            'strategies': strategies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Test basic LLM connection
        test_messages = [{'role': 'user', 'content': 'Hello'}]
        test_config = {'model': 'gpt-4', 'temperature': 0, 'max_tokens': 5}
        response = client.generate_content_with_messages(test_messages, **test_config)
        
        # Get system stats
        collections = doc_processor.get_collections()
        sessions = conversation_manager.list_sessions()
        
        return jsonify({
            'status': 'healthy',
            'components': {
                'pikerag_initialized': client is not None,
                'azure_openai_connected': bool(response),
                'document_processor': doc_processor is not None,
                'conversation_manager': conversation_manager is not None,
                'reasoning_manager': reasoning_manager is not None
            },
            'stats': {
                'knowledge_bases': len(collections),
                'active_sessions': len(sessions),
                'total_collections_documents': sum(kb['count'] for kb in collections)
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/examples')
def get_examples():
    """Get enhanced example questions with reasoning strategies"""
    examples = [
        {
            'category': 'Simple Questions (Generation)',
            'strategy': 'generation',
            'questions': [
                'What is the capital of France?',
                'Who invented the telephone?',
                'What is photosynthesis?'
            ]
        },
        {
            'category': 'Complex Reasoning (Self-Ask)', 
            'strategy': 'self_ask',
            'questions': [
                'How would climate change affect agricultural productivity in developing countries?',
                'What are the economic implications of widespread adoption of renewable energy?',
                'If I invest $1000 in a stock that grows 5% annually, how much will I have in 10 years, and what factors could affect this?'
            ]
        },
        {
            'category': 'Multi-Step Problems (Atomic Decomposition)',
            'strategy': 'atomic_decomposition', 
            'questions': [
                'Compare the environmental impact of electric cars versus gasoline cars, considering manufacturing, usage, and disposal.',
                'Analyze the factors that led to the fall of the Roman Empire and their relevance to modern democracies.',
                'What would be the steps to implement a machine learning system for fraud detection in a bank?'
            ]
        }
    ]
    
    return jsonify(examples)

if __name__ == '__main__':
    print("🚀 Starting PIKE-RAG Enhanced Web Application...")
    
    if initialize_pikerag():
        print("🌐 Enhanced web app running at: http://localhost:5001")
        print("📚 Features: Document Upload, Multi-turn Conversations, Advanced Reasoning")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ Failed to start enhanced web application")
        sys.exit(1)