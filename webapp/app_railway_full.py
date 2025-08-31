#!/usr/bin/env python3
"""
PIKE-RAG Full-Featured Web Application for Railway
Preserves all original features with lightweight alternatives
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Core imports
from pikerag.utils.logger import Logger
from pikerag.workflows.common import GenerationQaData

# Lightweight alternatives
from document_processor_lite import DocumentProcessorLite
from conversation_manager import ConversationManager

# Import reasoning strategies with fallbacks
try:
    from reasoning_strategies import ReasoningStrategyManager
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    print("⚠️  Advanced reasoning strategies not available")

# OpenAI client setup
import openai

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
KNOWLEDGE_BASE_FOLDER = os.path.join(os.path.dirname(__file__), 'knowledge_base')
SESSIONS_FOLDER = os.path.join(os.path.dirname(__file__), 'sessions')

# Global variables
openai_client = None
logger = None
doc_processor = None
conversation_manager = None
reasoning_manager = None
azure_deployment_name = None

def initialize_railway_full():
    """Initialize full-featured PIKE-RAG for Railway"""
    global openai_client, logger, doc_processor, conversation_manager, reasoning_manager, azure_deployment_name
    
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
        for folder in [UPLOAD_FOLDER, KNOWLEDGE_BASE_FOLDER, SESSIONS_FOLDER]:
            os.makedirs(folder, exist_ok=True)
        
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize logger
        logger = Logger(name='railway_full', dump_folder=log_dir, dump_mode='a')
        
        # Initialize OpenAI client
        if os.environ.get('OPENAI_API_TYPE') == 'azure':
            openai_client = openai.AzureOpenAI(
                azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
                api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
                api_version=os.environ.get('OPENAI_API_VERSION', '2024-08-01-preview')
            )
            # Store the deployment name for Azure OpenAI
            azure_deployment_name = os.environ.get('AZURE_DEPLOYMENT_NAME', 'gpt-4')
            print("✅ Azure OpenAI client initialized")
        else:
            openai_client = openai.OpenAI(
                api_key=os.environ.get('OPENAI_API_KEY')
            )
            # Use standard model name for non-Azure OpenAI
            azure_deployment_name = 'gpt-4'
            print("✅ Standard OpenAI client initialized")
        
        # Initialize components with lightweight alternatives
        azure_embedding_deployment = os.environ.get('AZURE_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
        doc_processor = DocumentProcessorLite(
            UPLOAD_FOLDER, 
            KNOWLEDGE_BASE_FOLDER, 
            openai_client,
            azure_embedding_deployment
        )
        
        conversation_manager = ConversationManager(SESSIONS_FOLDER)
        
        if REASONING_AVAILABLE:
            reasoning_manager = ReasoningStrategyManager()
            print("✅ Advanced reasoning strategies loaded")
        else:
            # Create a simple reasoning manager placeholder with required methods
            class SimpleReasoningManager:
                def __init__(self):
                    self.available = True
                    self.strategies = ['generation', 'self_ask', 'atomic_decomposition']
                
                def process_with_strategy(self, strategy_name, question, context, conversation_history=None, llm_client=None):
                    """Fallback processing - use basic generation with context"""
                    try:
                        # Use the same generate_simple_answer function that's already implemented
                        answer = generate_simple_answer(question, context or [], conversation_history or [])
                        return {
                            'answer': answer,
                            'rationale': f'Used basic generation (advanced {strategy_name} not available)',
                            'confidence': 0.7
                        }
                    except Exception as e:
                        return {
                            'answer': f'Error in fallback reasoning: {str(e)}',
                            'rationale': f'Fallback failed for {strategy_name}',
                            'confidence': 0.1
                        }
            
            reasoning_manager = SimpleReasoningManager()
            print("✅ Basic reasoning strategies loaded")
        
        print("✅ Full-featured PIKE-RAG for Railway initialized")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
def index():
    """Main page with full features"""
    try:
        return render_template('index_enhanced.html')
    except:
        # Fallback to embedded HTML if template missing
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🚀 PIKE-RAG Full (Railway)</title>
            <style>
                /* Modern styling */
                * { box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0; padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container { 
                    max-width: 1200px; margin: 0 auto; 
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px; padding: 40px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                .feature-grid { 
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; margin: 30px 0; 
                }
                .feature-card { 
                    background: #f8f9ff; padding: 25px; border-radius: 15px;
                    border-left: 5px solid #667eea;
                }
                h1 { color: #333; text-align: center; margin-bottom: 10px; font-size: 2.5em; }
                .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 1.1em; }
                input, textarea, select { 
                    width: 100%; padding: 12px; border: 2px solid #e1e5e9;
                    border-radius: 8px; font-size: 14px; margin: 8px 0;
                }
                button { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 12px 25px; border: none; 
                    border-radius: 8px; cursor: pointer; font-weight: 600;
                    margin: 5px;
                }
                button:hover { opacity: 0.9; }
                .status { 
                    background: #e8f5e8; color: #2d5a2d; padding: 15px;
                    border-radius: 10px; margin: 20px 0; text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 PIKE-RAG Full</h1>
                <p class="subtitle">Railway Deployment • All Features Enabled</p>
                
                <div class="status">
                    ✅ Document Upload • 💬 Conversations • 🧠 Advanced Reasoning • 🔍 Knowledge Search
                </div>
                
                <div class="feature-grid">
                    <!-- Document Upload -->
                    <div class="feature-card">
                        <h3>📄 Document Upload</h3>
                        <input type="file" id="fileInput" accept=".txt,.pdf,.docx" />
                        <button onclick="uploadDocument()">Upload Document</button>
                        <div id="uploadStatus"></div>
                    </div>
                    
                    <!-- Question Asking -->
                    <div class="feature-card">
                        <h3>💬 Ask Questions</h3>
                        <select id="reasoningStrategy">
                            <option value="generation">Direct Generation</option>
                            <option value="self_ask">Self-Ask Reasoning</option>
                            <option value="atomic">Atomic Decomposition</option>
                        </select>
                        <textarea id="question" rows="3" placeholder="Ask your question..."></textarea>
                        <button onclick="askQuestion()">Ask Question</button>
                    </div>
                    
                    <!-- Session Management -->
                    <div class="feature-card">
                        <h3>🗨️ Conversations</h3>
                        <button onclick="startNewSession()">New Conversation</button>
                        <button onclick="showSessions()">View Sessions</button>
                        <div id="sessionInfo"></div>
                    </div>
                    
                    <!-- Document Library -->
                    <div class="feature-card">
                        <h3>📚 Document Library</h3>
                        <button onclick="showDocuments()">View Documents</button>
                        <div id="documentsInfo"></div>
                    </div>
                </div>
                
                <div id="response" style="margin-top: 30px; display: none;"></div>
            </div>

            <script>
                let currentSessionId = null;
                
                async function uploadDocument() {
                    const fileInput = document.getElementById('fileInput');
                    const statusDiv = document.getElementById('uploadStatus');
                    
                    if (!fileInput.files[0]) {
                        alert('Please select a file');
                        return;
                    }
                    
                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);
                    
                    statusDiv.innerHTML = '<p style="color: #667eea;">⏳ Uploading...</p>';
                    
                    try {
                        const response = await fetch('/api/upload', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            statusDiv.innerHTML = `
                                <div style="color: #2d5a2d; background: #e8f5e8; padding: 10px; border-radius: 5px;">
                                    ✅ Uploaded: ${data.filename}<br>
                                    📊 ${data.chunks} chunks processed
                                </div>
                            `;
                        } else {
                            statusDiv.innerHTML = `<p style="color: #d32f2f;">❌ ${data.error}</p>`;
                        }
                    } catch (error) {
                        statusDiv.innerHTML = `<p style="color: #d32f2f;">❌ Upload failed: ${error.message}</p>`;
                    }
                }
                
                async function askQuestion() {
                    const question = document.getElementById('question').value.trim();
                    const strategy = document.getElementById('reasoningStrategy').value;
                    const responseDiv = document.getElementById('response');
                    
                    if (!question) {
                        alert('Please enter a question');
                        return;
                    }
                    
                    responseDiv.style.display = 'block';
                    responseDiv.innerHTML = '<div style="color: #667eea;">🤔 Processing...</div>';
                    
                    try {
                        const response = await fetch('/api/ask', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                question: question,
                                reasoning_strategy: strategy,
                                session_id: currentSessionId,
                                use_retrieval: true
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            responseDiv.innerHTML = `
                                <div style="background: #f8f9ff; padding: 25px; border-radius: 15px; border-left: 5px solid #667eea;">
                                    <h4>💬 Question</h4>
                                    <p style="background: white; padding: 15px; border-radius: 8px;">${data.question}</p>
                                    <h4>🤖 Answer</h4>
                                    <div style="background: white; padding: 15px; border-radius: 8px; line-height: 1.6;">
                                        ${data.answer.replace(/\\n/g, '<br>')}
                                    </div>
                                    <p style="color: #666; font-size: 0.9em; margin-top: 15px;">
                                        ⚡ ${data.processing_time}s • 🧠 ${strategy} • 
                                        📚 ${data.sources_used || 0} sources • 
                                        🚀 Railway Full
                                    </p>
                                </div>
                            `;
                            currentSessionId = data.session_id;
                        } else {
                            responseDiv.innerHTML = `<div style="color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px;">❌ ${data.error}</div>`;
                        }
                    } catch (error) {
                        responseDiv.innerHTML = `<div style="color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px;">🌐 Error: ${error.message}</div>`;
                    }
                }
                
                async function startNewSession() {
                    const response = await fetch('/api/session/new', { method: 'POST' });
                    const data = await response.json();
                    currentSessionId = data.session_id;
                    document.getElementById('sessionInfo').innerHTML = `<p style="color: #2d5a2d;">✅ New session: ${currentSessionId.substr(0, 8)}...</p>`;
                }
                
                async function showDocuments() {
                    try {
                        const response = await fetch('/api/documents');
                        const documents = await response.json();
                        
                        let html = '<div style="margin-top: 10px;">';
                        if (documents.length === 0) {
                            html += '<p>No documents uploaded yet.</p>';
                        } else {
                            documents.forEach(doc => {
                                html += `
                                    <div style="background: white; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #667eea;">
                                        <strong>${doc.name}</strong><br>
                                        <small>${doc.chunks} chunks • ${doc.processed_at}</small>
                                    </div>
                                `;
                            });
                        }
                        html += '</div>';
                        
                        document.getElementById('documentsInfo').innerHTML = html;
                    } catch (error) {
                        document.getElementById('documentsInfo').innerHTML = `<p style="color: #d32f2f;">Error: ${error.message}</p>`;
                    }
                }
                
                // Initialize
                startNewSession();
            </script>
        </body>
        </html>
        """

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload with full document processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file size (additional validation beyond Flask's MAX_CONTENT_LENGTH)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Seek back to beginning
        
        print(f"📄 Uploading file: {file.filename}, Size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        
        if file_size > 16 * 1024 * 1024:  # 16MB limit
            return jsonify({
                'success': False, 
                'error': f'File too large: {file_size/1024/1024:.2f}MB. Maximum allowed: 16MB'
            }), 400
        
        # Validate file type
        filename = secure_filename(file.filename)
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        supported_extensions = ['pdf', 'docx', 'txt']  # Removed 'doc' from supported
        
        if file_ext == 'doc':
            return jsonify({
                'success': False, 
                'error': 'Old Word format (.doc) is not supported. Please save your document as .docx format (Word 2007 or later) and try again.'
            }), 400
        
        if file_ext not in supported_extensions:
            return jsonify({
                'success': False, 
                'error': f'Unsupported file type: .{file_ext}. Supported: {", ".join(supported_extensions)}'
            }), 400
        
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        print(f"✅ File saved to: {filepath}")
        
        # Process document
        print(f"🔄 Processing document: {filename}")
        result = doc_processor.process_document(filepath, filename)
        
        if result['success']:
            print(f"✅ Document processed successfully: {result['chunks']} chunks created")
            return jsonify({
                'success': True,
                'filename': filename,
                'document_id': result['document_id'],
                'chunks': result['chunks'],
                'preview': result.get('text_preview', ''),
                'file_size_mb': round(file_size/1024/1024, 2)
            })
        else:
            print(f"❌ Document processing failed: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Enhanced question answering with all features"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        session_id = data.get('session_id')
        reasoning_strategy = data.get('reasoning_strategy', 'generation')
        use_retrieval = data.get('use_retrieval', True)
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        start_time = time.time()
        
        # Get or create session
        if not session_id:
            session_id = conversation_manager.create_session(reasoning_strategy)
        
        # Add user message to conversation
        conversation_manager.add_message(session_id, 'user', question)
        
        # Get conversation history as dictionaries for LLM
        history = conversation_manager.get_context_for_llm(session_id)
        
        # Retrieve relevant documents if requested
        sources = []
        if use_retrieval:
            search_results = doc_processor.search_documents(question, n_results=5)
            sources = [result['content'] for result in search_results if result['score'] > 0.5]
        
        # Generate response using appropriate strategy
        if reasoning_manager and reasoning_strategy != 'generation':
            # Use advanced reasoning if available
            try:
                result = reasoning_manager.process_with_strategy(
                    strategy_name=reasoning_strategy,
                    question=question,
                    context=sources,
                    conversation_history=history,
                    llm_client=openai_client,
                    llm_config={'model': 'gpt-4', 'temperature': 0.1, 'max_tokens': 1000}
                )
                answer = result.get('answer', 'No answer generated')
                rationale = result.get('rationale', '')
            except Exception as e:
                print(f"Advanced reasoning failed: {e}")
                # Fallback to simple generation
                answer = generate_simple_answer(question, sources, history)
                rationale = "Used fallback reasoning"
        else:
            # Simple generation
            answer = generate_simple_answer(question, sources, history)
            rationale = ""
        
        # Add assistant response to conversation
        conversation_manager.add_message(session_id, 'assistant', answer, {
            'reasoning_strategy': reasoning_strategy,
            'sources_used': len(sources),
            'processing_time': time.time() - start_time
        })
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'rationale': rationale,
            'session_id': session_id,
            'reasoning_strategy': reasoning_strategy,
            'sources_used': len(sources),
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'question': data.get('question', '') if 'data' in locals() else ''
        }), 500

def generate_simple_answer(question: str, sources: List[str], history: List[dict]) -> str:
    """Simple answer generation with context"""
    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately."}
        ]
        
        # Add conversation history (already formatted for LLM)
        messages.extend(history[-4:] if len(history) > 4 else history)
        
        # Add context if available
        if sources:
            context = "\\n\\nRelevant context:\\n" + "\\n".join(sources[:3])
            messages.append({"role": "user", "content": question + context})
        else:
            messages.append({"role": "user", "content": question})
        
        response = openai_client.chat.completions.create(
            messages=messages,
            model=azure_deployment_name,
            temperature=0.1,
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"

@app.route('/api/session/new', methods=['POST'])
def create_session():
    """Create new conversation session"""
    try:
        data = request.get_json() or {}
        reasoning_strategy = data.get('reasoning_strategy', 'generation')
        session_id = conversation_manager.create_session(reasoning_strategy)
        return jsonify({'session_id': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents')
def get_documents():
    """Get list of uploaded documents"""
    try:
        documents = doc_processor.get_available_documents()
        return jsonify(documents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/examples')
def get_examples():
    """Get example questions for the interface"""
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/info')
def get_system_info():
    """Get system information and feature status"""
    try:
        return jsonify({
            'status': 'operational',
            'version': 'railway-full-v1.0',
            'features': {
                'document_upload': doc_processor is not None,
                'conversation_management': conversation_manager is not None,
                'advanced_reasoning': reasoning_manager is not None,
                'vector_search': doc_processor.chroma_client is not None if doc_processor else False,
                'openai_integration': openai_client is not None
            },
            'capabilities': [
                'Document Processing (PDF, DOCX, TXT)',
                'Semantic Search with OpenAI Embeddings',
                'Multi-turn Conversations',
                'Advanced Reasoning Strategies',
                'Session Management',
                'Knowledge Base Management'
            ],
            'deployment': 'Railway',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/knowledge-bases')
def get_knowledge_bases():
    """Get available knowledge bases in the format expected by frontend"""
    try:
        if not doc_processor:
            return jsonify({'success': True, 'knowledge_bases': []})
        
        documents = doc_processor.get_available_documents()
        
        # Format knowledge bases as expected by frontend
        knowledge_bases = []
        
        if documents:
            for doc in documents:
                knowledge_bases.append({
                    'name': doc['name'],
                    'count': doc.get('chunks', 1),
                    'last_updated': doc.get('processed_at', 'Unknown')
                })
        
        # Add default if no documents
        if not knowledge_bases:
            knowledge_bases.append({
                'name': 'General Knowledge',
                'count': 0,
                'last_updated': 'Always available'
            })
        
        return jsonify({
            'success': True,
            'knowledge_bases': knowledge_bases
        })
        
    except Exception as e:
        print(f"Error getting knowledge bases: {e}")
        return jsonify({
            'success': True,
            'knowledge_bases': [{
                'name': 'General Knowledge',
                'count': 0,
                'last_updated': 'Fallback mode'
            }]
        })

@app.route('/api/sessions')
def get_sessions():
    """Get conversation sessions"""
    try:
        if not conversation_manager:
            return jsonify({'success': True, 'sessions': []})
        
        # Use the built-in list_sessions method
        sessions_data = conversation_manager.list_sessions()
        
        return jsonify({
            'success': True,
            'sessions': sessions_data
        })
        
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return jsonify({
            'success': True,
            'sessions': []
        })

@app.route('/api/knowledge-bases/<collection_name>/files')
def get_knowledge_base_files(collection_name):
    """Get files in a specific knowledge base collection"""
    try:
        if not doc_processor or not doc_processor.chroma_client:
            return jsonify({
                'success': False,
                'error': 'Document processor not available'
            }), 400
        
        # Get collection details
        try:
            collection = doc_processor.chroma_client.get_collection(collection_name)
            
            # Get all documents in the collection
            results = collection.get(include=['metadatas', 'documents'])
            
            # Group by filename
            files_dict = {}
            for i, metadata in enumerate(results['metadatas']):
                filename = metadata.get('filename', 'Unknown')
                if filename not in files_dict:
                    files_dict[filename] = {
                        'filename': filename,
                        'chunks_count': 0,
                        'file_type': metadata.get('file_type', 'unknown'),
                        'processed_at': metadata.get('processed_at', 'Unknown')
                    }
                files_dict[filename]['chunks_count'] += 1
            
            files_list = list(files_dict.values())
            
            return jsonify({
                'success': True,
                'collection_name': collection_name,
                'files': files_list,
                'total_chunks': collection.count()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Collection not found: {str(e)}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reasoning-strategies')
def get_reasoning_strategies():
    """Get available reasoning strategies"""
    try:
        strategies = [
            {
                'id': 'generation',
                'name': 'Direct Answer',
                'description': 'Direct question answering with retrieved context',
                'available': True
            },
            {
                'id': 'self_ask',
                'name': 'Self-Ask Reasoning',
                'description': 'Self-questioning reasoning chains for step-by-step problem solving',
                'available': reasoning_manager is not None
            },
            {
                'id': 'atomic_decomposition',
                'name': 'Atomic Decomposition',
                'description': 'Break complex questions into atomic sub-questions',
                'available': reasoning_manager is not None
            }
        ]
        
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
    """Health check with system information for settings page"""
    try:
        # Test OpenAI connection
        try:
            test_response = openai_client.chat.completions.create(
                messages=[{"role": "user", "content": "Hi"}],
                model=azure_deployment_name,
                max_tokens=5
            )
            openai_connected = True
        except:
            openai_connected = False
        
        # Get stats
        knowledge_bases_count = 0
        active_sessions_count = 0
        total_documents = 0
        
        if doc_processor:
            documents = doc_processor.get_available_documents()
            total_documents = len(documents)
            knowledge_bases_count = 1 if documents else 1  # General knowledge always available
            
        if conversation_manager and hasattr(conversation_manager, 'sessions_dir') and os.path.exists(conversation_manager.sessions_dir):
            active_sessions_count = len([f for f in os.listdir(conversation_manager.sessions_dir) if f.endswith('.json')])
        
        return jsonify({
            'status': 'healthy',
            'version': 'railway-full-v1.0',
            'deployment': 'Railway',
            'stats': {
                'knowledge_bases': knowledge_bases_count,
                'active_sessions': active_sessions_count,
                'total_collections_documents': total_documents
            },
            'features': {
                'document_upload': doc_processor is not None,
                'conversation_management': conversation_manager is not None,
                'advanced_reasoning': reasoning_manager is not None,
                'vector_search': doc_processor.chroma_client is not None if doc_processor else False,
                'openai_integration': openai_connected
            },
            'components': {
                'pikerag_initialized': True,  # App is running so core is initialized
                'azure_openai_connected': openai_connected,
                'document_processor': doc_processor is not None,
                'conversation_manager': conversation_manager is not None,
                'reasoning_manager': reasoning_manager is not None
            },
            'openai_connected': openai_connected,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'stats': {
                'knowledge_bases': 0,
                'active_sessions': 0,  
                'total_collections_documents': 0
            },
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Full-Featured PIKE-RAG for Railway...")
    
    if initialize_railway_full():
        port = int(os.environ.get('PORT', 5001))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        print(f"🌐 Full-featured PIKE-RAG running on port {port}")
        app.run(debug=debug, host='0.0.0.0', port=port)
    else:
        print("❌ Failed to start application")
        sys.exit(1)