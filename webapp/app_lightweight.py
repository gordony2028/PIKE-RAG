#!/usr/bin/env python3
"""
PIKE-RAG Lightweight Web Application for Railway Deployment
Minimal dependencies version - no heavy ML libraries
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only lightweight components
from pikerag.llm_client.azure_open_ai_client import AzureOpenAIClient
from pikerag.utils.logger import Logger
from pikerag.workflows.common import GenerationQaData
from pikerag.prompts.qa.generation import generation_qa_protocol

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
client = None
logger = None

def initialize_pikerag():
    """Initialize lightweight PIKE-RAG components"""
    global client, logger
    
    try:
        # Load environment variables from Railway or local
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            print("✅ Running on Railway - using environment variables")
        else:
            # Try loading from .env file for local development
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print("✅ Loaded local environment variables")
            except ImportError:
                print("⚠️  python-dotenv not available, using system env vars")
        
        # Create logs directory
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Simple logger (Railway deployment compatible)
        logger = Logger(name='webapp', dump_folder=log_dir, dump_mode='a')
        
        # Initialize LLM client with Railway-compatible cache
        cache_path = os.path.join(log_dir, 'webapp_cache.db')
        client = AzureOpenAIClient(
            location=cache_path,
            auto_dump=True,
            logger=logger
        )
        
        print("✅ Lightweight PIKE-RAG components initialized")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """API endpoint for asking questions"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Create QA data
        qa_data = GenerationQaData(question=question)
        
        # Process with lightweight protocol (no retrieval)
        start_time = time.time()
        
        protocol = generation_qa_protocol
        messages = protocol.process_input(
            content=qa_data.question,
            references=[],  # No retrieval for lightweight version
            **qa_data.as_dict()
        )
        
        # LLM configuration
        llm_config = {
            'model': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 500
        }
        
        # Get response
        response = client.generate_content_with_messages(messages, **llm_config)
        output_dict = protocol.parse_output(response, **qa_data.as_dict())
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': output_dict.get('answer', 'No answer generated'),
            'rationale': output_dict.get('rationale', ''),
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat(),
            'model': llm_config['model'],
            'note': 'Lightweight deployment - basic QA only'
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'question': data.get('question', '') if 'data' in locals() else ''
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Simple health check
        test_messages = [{'role': 'user', 'content': 'Hello'}]
        test_config = {'model': 'gpt-4', 'temperature': 0, 'max_tokens': 5}
        
        response = client.generate_content_with_messages(test_messages, **test_config)
        
        return jsonify({
            'status': 'healthy',
            'version': 'lightweight',
            'pikerag_initialized': client is not None,
            'azure_openai_connected': bool(response),
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
    """Get example questions"""
    examples = [
        {
            'category': 'General Knowledge',
            'questions': [
                'What is the capital of France?',
                'Who invented the telephone?',
                'What is the largest planet in our solar system?'
            ]
        },
        {
            'category': 'Science',
            'questions': [
                'What is photosynthesis?',
                'How does DNA replication work?',
                'What causes earthquakes?'
            ]
        },
        {
            'category': 'Technology',
            'questions': [
                'What is artificial intelligence?',
                'How does machine learning work?',
                'What is the difference between HTTP and HTTPS?'
            ]
        }
    ]
    return jsonify(examples)

if __name__ == '__main__':
    print("🚀 Starting Lightweight PIKE-RAG Web Application...")
    
    if initialize_pikerag():
        port = int(os.environ.get('PORT', 5001))
        debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
        
        print(f"🌐 Lightweight web app running on port: {port}")
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        print("❌ Failed to start application")
        sys.exit(1)