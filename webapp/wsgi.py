#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment - Minimal version
"""
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use minimal app to avoid transformers dependency
from app_minimal import app, initialize_minimal

# Initialize components
if not initialize_minimal():
    print("❌ Failed to initialize minimal components")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)