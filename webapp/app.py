#!/usr/bin/env python3
"""
PIKE-RAG Custom Web Application
Built with Flask and integrated with Azure OpenAI
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, stream_template
from flask_cors import CORS

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pikerag.utils.config_loader import load_dot_env
from pikerag.llm_client.azure_open_ai_client import AzureOpenAIClient
from pikerag.utils.logger import Logger
from pikerag.workflows.common import GenerationQaData
from pikerag.prompts.qa.generation import generation_qa_protocol

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls

# Global variables for PIKE-RAG components
client = None
logger = None

def initialize_pikerag():
    """Initialize PIKE-RAG components"""
    global client, logger
    
    try:
        # Load environment variables - try multiple locations
        env_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env_configs', '.env'),
            os.path.join(os.path.dirname(__file__), '.env'),
            '.env'
        ]
        
        env_loaded = False
        for env_path in env_paths:
            if os.path.exists(env_path):
                try:
                    load_dot_env(env_path)
                    env_loaded = True
                    print(f"✅ Loaded environment from: {env_path}")
                    break
                except Exception as e:
                    print(f"⚠️  Failed to load {env_path}: {e}")
                    continue
        
        # For Railway deployment, environment variables are set directly
        if not env_loaded and os.environ.get('RAILWAY_ENVIRONMENT'):
            print("✅ Running on Railway - using environment variables")
            env_loaded = True
        elif not env_loaded:
            print("⚠️  No .env file found - ensure environment variables are set")
        
        # Create logger
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logger = Logger(name='webapp', dump_folder=log_dir, dump_mode='a')
        
        # Initialize Azure OpenAI client
        cache_path = os.path.join(log_dir, 'webapp_cache.db')
        client = AzureOpenAIClient(
            location=cache_path,
            auto_dump=True,
            logger=logger
        )
        
        print("✅ PIKE-RAG components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize PIKE-RAG: {e}")
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
        
        # Process through PIKE-RAG
        start_time = time.time()
        
        # Use generation protocol (no retrieval for simplicity)
        protocol = generation_qa_protocol
        messages = protocol.process_input(
            content=qa_data.question,
            references=[],  # No retrieval context for this simple version
            **qa_data.as_dict()
        )
        
        # LLM configuration
        llm_config = {
            'model': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 500
        }
        
        # Get response from LLM
        response = client.generate_content_with_messages(messages, **llm_config)
        
        # Parse output
        output_dict = protocol.parse_output(response, **qa_data.as_dict())
        
        processing_time = time.time() - start_time
        
        # Prepare response
        result = {
            'success': True,
            'question': question,
            'answer': output_dict.get('answer', 'No answer generated'),
            'rationale': output_dict.get('rationale', ''),
            'raw_response': response,
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat(),
            'model': llm_config['model']
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'question': data.get('question', '') if 'data' in locals() else ''
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Simple test to verify Azure OpenAI connection
        test_messages = [{'role': 'user', 'content': 'Hello'}]
        test_config = {'model': 'gpt-4', 'temperature': 0, 'max_tokens': 5}
        
        response = client.generate_content_with_messages(test_messages, **test_config)
        
        return jsonify({
            'status': 'healthy',
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
        },
        {
            'category': 'Complex Reasoning',
            'questions': [
                'If I have 3 apples and give away 2, then buy 5 more, how many do I have?',
                'What are the pros and cons of renewable energy?',
                'How might climate change affect food production?'
            ]
        }
    ]
    
    return jsonify(examples)

if __name__ == '__main__':
    print("🚀 Starting PIKE-RAG Web Application...")
    
    if initialize_pikerag():
        # Get port from environment variable (Railway sets PORT)
        port = int(os.environ.get('PORT', 5001))
        debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
        
        print(f"🌐 Web app running on port: {port}")
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        print("❌ Failed to start web application")
        sys.exit(1)