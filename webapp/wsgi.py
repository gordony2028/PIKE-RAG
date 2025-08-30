#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment - Lightweight version
"""
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use lightweight app for Railway deployment
from app_lightweight import app, initialize_pikerag

# Initialize components
if not initialize_pikerag():
    print("❌ Failed to initialize PIKE-RAG components")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)