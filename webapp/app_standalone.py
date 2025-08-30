#!/usr/bin/env python3
"""
Standalone PIKE-RAG Web Application for Railway
No PIKE-RAG imports - direct OpenAI integration
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openai
import pickle
from typing import Dict, Any

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
openai_client = None
cache = {}
cache_file = None

def load_cache():
    """Load response cache"""
    global cache, cache_file
    try:
        cache_file = os.path.join(os.path.dirname(__file__), 'logs', 'openai_cache.pkl')
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                cache = pickle.load(f)
            print(f"✅ Loaded {len(cache)} cached responses")
        else:
            cache = {}
            print("✅ Cache initialized")
    except Exception as e:
        print(f"⚠️  Cache load error: {e}")
        cache = {}

def save_cache():
    """Save response cache"""
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(cache, f)
    except Exception as e:
        print(f"⚠️  Cache save error: {e}")

def get_cache_key(messages: list, **kwargs) -> str:
    """Generate cache key for request"""
    return hash(json.dumps({"messages": messages, **kwargs}, sort_keys=True))

def initialize_standalone():
    """Initialize standalone OpenAI client"""
    global openai_client
    
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
        
        # Load cache
        load_cache()
        
        # Check for Azure OpenAI configuration
        if os.environ.get('OPENAI_API_TYPE') == 'azure':
            print("🔧 Configuring Azure OpenAI...")
            openai_client = openai.AzureOpenAI(
                azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
                api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
                api_version=os.environ.get('OPENAI_API_VERSION', '2024-08-01-preview')
            )
            print("✅ Azure OpenAI client initialized")
        else:
            # Standard OpenAI
            print("🔧 Configuring Standard OpenAI...")
            openai_client = openai.OpenAI(
                api_key=os.environ.get('OPENAI_API_KEY')
            )
            print("✅ Standard OpenAI client initialized")
        
        # Test connection
        test_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print("✅ OpenAI connection verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def chat_with_openai(messages: list, **kwargs) -> str:
    """Chat with OpenAI with caching"""
    try:
        # Check cache
        cache_key = get_cache_key(messages, **kwargs)
        if cache_key in cache:
            print("📋 Cache hit")
            return cache[cache_key]
        
        # Make API call
        response = openai_client.chat.completions.create(
            messages=messages,
            **kwargs
        )
        
        result = response.choices[0].message.content.strip()
        
        # Cache the result
        cache[cache_key] = result
        save_cache()
        
        return result
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        raise

@app.route('/')
def index():
    """Main page with embedded UI"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 PIKE-RAG on Railway</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6; margin: 0; padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 900px; margin: 0 auto; 
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px; padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 { color: #333; text-align: center; margin-bottom: 10px; font-size: 2.5em; }
            .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 1.1em; }
            .input-group { margin: 20px 0; }
            label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
            input[type="text"] { 
                width: 100%; padding: 15px; border: 2px solid #e1e5e9;
                border-radius: 10px; font-size: 16px;
                transition: border-color 0.3s ease;
            }
            input[type="text"]:focus { 
                outline: none; border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            button { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 15px 30px; border: none; 
                border-radius: 10px; cursor: pointer; font-size: 16px;
                font-weight: 600; transition: transform 0.2s ease;
                width: 100%;
            }
            button:hover { transform: translateY(-2px); }
            button:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
            #response { 
                margin-top: 30px; padding: 25px; 
                background: #f8f9ff; border-radius: 15px;
                border-left: 5px solid #667eea; display: none;
            }
            .examples { margin: 30px 0; }
            .examples h3 { color: #333; margin-bottom: 15px; }
            .example { 
                background: #f1f3f4; padding: 15px; margin: 8px 0; 
                border-radius: 8px; cursor: pointer; 
                transition: all 0.2s ease; border: 2px solid transparent;
            }
            .example:hover { 
                background: #e8f0fe; border-color: #667eea;
                transform: translateY(-1px);
            }
            .loading { 
                display: flex; align-items: center; gap: 10px;
                color: #667eea; font-weight: 500;
            }
            .spinner { 
                width: 20px; height: 20px; border: 2px solid #e1e5e9;
                border-top: 2px solid #667eea; border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .status { 
                background: #e8f5e8; color: #2d5a2d; padding: 10px;
                border-radius: 8px; margin-bottom: 20px; text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 PIKE-RAG</h1>
            <p class="subtitle">Deployed on Railway • Powered by Azure OpenAI</p>
            
            <div class="status">
                ✅ Connected to OpenAI • Response caching enabled
            </div>
            
            <div class="input-group">
                <label for="question">Ask any question:</label>
                <input type="text" id="question" placeholder="What would you like to know?" />
            </div>
            
            <button onclick="askQuestion()" id="askBtn">Ask Question</button>
            
            <div class="examples">
                <h3>💡 Try these examples:</h3>
                <div class="example" onclick="setQuestion(this.textContent)">
                    What is the difference between machine learning and deep learning?
                </div>
                <div class="example" onclick="setQuestion(this.textContent)">
                    Explain quantum computing in simple terms
                </div>
                <div class="example" onclick="setQuestion(this.textContent)">
                    How does blockchain technology work?
                </div>
                <div class="example" onclick="setQuestion(this.textContent)">
                    What are the benefits of renewable energy?
                </div>
            </div>
            
            <div id="response"></div>
        </div>

        <script>
            function setQuestion(text) {
                document.getElementById('question').value = text;
                document.getElementById('question').focus();
            }
            
            async function askQuestion() {
                const question = document.getElementById('question').value.trim();
                if (!question) {
                    alert('Please enter a question');
                    return;
                }
                
                const responseDiv = document.getElementById('response');
                const askBtn = document.getElementById('askBtn');
                
                // Show loading state
                responseDiv.style.display = 'block';
                responseDiv.innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>Thinking...</span>
                    </div>
                `;
                askBtn.disabled = true;
                askBtn.textContent = 'Processing...';
                
                try {
                    const startTime = Date.now();
                    const response = await fetch('/api/ask', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: question })
                    });
                    
                    const data = await response.json();
                    const endTime = Date.now();
                    
                    if (data.success) {
                        responseDiv.innerHTML = `
                            <h4 style="color: #333; margin-top: 0;">💬 Question</h4>
                            <p style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
                                ${data.question}
                            </p>
                            <h4 style="color: #333;">🤖 Answer</h4>
                            <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0; line-height: 1.7;">
                                ${data.answer.replace(/\\n/g, '<br>')}
                            </div>
                            <p style="color: #666; font-size: 0.9em; margin-top: 15px;">
                                ⚡ ${data.processing_time}s • 🤖 ${data.model} • 
                                ${data.cached ? '📋 Cached' : '🔄 Live'} • 
                                🚀 Railway Deployment
                            </p>
                        `;
                    } else {
                        responseDiv.innerHTML = `
                            <div style="color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px;">
                                <strong>❌ Error:</strong> ${data.error}
                            </div>
                        `;
                    }
                } catch (error) {
                    responseDiv.innerHTML = `
                        <div style="color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px;">
                            <strong>🌐 Network Error:</strong> ${error.message}
                        </div>
                    `;
                } finally {
                    askBtn.disabled = false;
                    askBtn.textContent = 'Ask Question';
                }
            }
            
            // Enter key support
            document.getElementById('question').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    askQuestion();
                }
            });
            
            // Focus input on load
            document.getElementById('question').focus();
        </script>
    </body>
    </html>
    """

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Standalone question answering"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        start_time = time.time()
        
        # Simple conversation
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and informative answers."},
            {"role": "user", "content": question}
        ]
        
        # Check cache first
        cache_key = get_cache_key(messages, model="gpt-4", temperature=0.1, max_tokens=800)
        cached = cache_key in cache
        
        # Get response
        response = chat_with_openai(
            messages=messages,
            model="gpt-4",
            temperature=0.1,
            max_tokens=800
        )
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': response,
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat(),
            'model': 'gpt-4',
            'deployment': 'railway-standalone',
            'cached': cached
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
    """Health check"""
    try:
        test_response = chat_with_openai(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4",
            max_tokens=5
        )
        
        return jsonify({
            'status': 'healthy',
            'version': 'standalone',
            'connected': bool(test_response),
            'cache_size': len(cache),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get deployment stats"""
    return jsonify({
        'deployment': 'Railway',
        'version': 'standalone',
        'cache_size': len(cache),
        'uptime': 'running',
        'features': [
            'Azure OpenAI Integration',
            'Response Caching', 
            'Embedded UI',
            'Health Monitoring'
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting Standalone PIKE-RAG for Railway...")
    
    if initialize_standalone():
        port = int(os.environ.get('PORT', 5001))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        print(f"🌐 Standalone app running on port {port}")
        app.run(debug=debug, host='0.0.0.0', port=port)
    else:
        print("❌ Failed to start")
        sys.exit(1)