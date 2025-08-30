#!/usr/bin/env python3
"""
PIKE-RAG Minimal Web Application for Railway Deployment
Direct imports to avoid heavy dependencies
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

# Direct imports to avoid __init__.py that imports transformers
from pikerag.llm_client.azure_open_ai_client import AzureOpenAIClient
from pikerag.utils.logger import Logger

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
client = None
logger = None

def initialize_minimal():
    """Initialize minimal components for Railway deployment"""
    global client, logger
    
    try:
        # Environment setup
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            print("✅ Railway environment detected")
        else:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print("✅ Local environment loaded")
            except:
                print("⚠️  Using system environment variables")
        
        # Create directories
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Simple logger
        logger = Logger(name='minimal', dump_folder=log_dir, dump_mode='a')
        
        # Azure OpenAI client (direct import, no package init)
        cache_path = os.path.join(log_dir, 'minimal_cache.db')
        client = AzureOpenAIClient(
            location=cache_path,
            auto_dump=True,
            logger=logger
        )
        
        print("✅ Minimal PIKE-RAG initialized")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
def index():
    """Main page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PIKE-RAG Minimal</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
            input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            #response { margin-top: 20px; padding: 20px; background: white; border-radius: 5px; border-left: 4px solid #007bff; }
            .example { background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 3px; cursor: pointer; }
            .example:hover { background: #dee2e6; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 PIKE-RAG Minimal</h1>
            <p>Lightweight deployment on Railway - Ask any question!</p>
            
            <input type="text" id="question" placeholder="Enter your question here..." />
            <button onclick="askQuestion()">Ask Question</button>
            
            <h3>Example Questions:</h3>
            <div class="example" onclick="setQuestion(this.textContent)">What is artificial intelligence?</div>
            <div class="example" onclick="setQuestion(this.textContent)">How does machine learning work?</div>
            <div class="example" onclick="setQuestion(this.textContent)">What is the capital of Japan?</div>
            
            <div id="response" style="display:none;"></div>
        </div>

        <script>
            function setQuestion(text) {
                document.getElementById('question').value = text;
            }
            
            async function askQuestion() {
                const question = document.getElementById('question').value.trim();
                if (!question) {
                    alert('Please enter a question');
                    return;
                }
                
                const responseDiv = document.getElementById('response');
                responseDiv.style.display = 'block';
                responseDiv.innerHTML = '<p>🤔 Thinking...</p>';
                
                try {
                    const response = await fetch('/api/ask', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ question: question })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        responseDiv.innerHTML = `
                            <h4>Question: ${data.question}</h4>
                            <p><strong>Answer:</strong> ${data.answer}</p>
                            <p><small>Processing time: ${data.processing_time}s | Model: ${data.model}</small></p>
                        `;
                    } else {
                        responseDiv.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    }
                } catch (error) {
                    responseDiv.innerHTML = `<p style="color: red;">Network error: ${error.message}</p>`;
                }
            }
            
            // Allow Enter key to submit
            document.getElementById('question').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    askQuestion();
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Minimal question answering endpoint"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        start_time = time.time()
        
        # Simple direct LLM call without PIKE-RAG protocols
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate answers to questions."},
            {"role": "user", "content": question}
        ]
        
        # LLM configuration
        llm_config = {
            'model': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 500
        }
        
        # Get response directly
        response = client.generate_content_with_messages(messages, **llm_config)
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': response.strip(),
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat(),
            'model': llm_config['model'],
            'deployment': 'minimal-railway'
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
        # Quick test
        test_messages = [{"role": "user", "content": "Hi"}]
        response = client.generate_content_with_messages(test_messages, model='gpt-4', max_tokens=5)
        
        return jsonify({
            'status': 'healthy',
            'version': 'minimal',
            'connected': bool(response),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Minimal PIKE-RAG for Railway...")
    
    if initialize_minimal():
        port = int(os.environ.get('PORT', 5001))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        print(f"🌐 Running on port {port}")
        app.run(debug=debug, host='0.0.0.0', port=port)
    else:
        print("❌ Failed to start")
        sys.exit(1)