#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment - Standalone version
"""
import os
import sys

# Use completely standalone app - no PIKE-RAG imports
from app_standalone import app, initialize_standalone

# Initialize components
if not initialize_standalone():
    print("❌ Failed to initialize standalone components")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)