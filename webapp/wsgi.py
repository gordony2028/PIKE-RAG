#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, initialize_pikerag

# Initialize PIKE-RAG components for production
if not initialize_pikerag():
    print("❌ Failed to initialize PIKE-RAG components")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)