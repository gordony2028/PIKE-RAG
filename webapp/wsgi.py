#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment - Full-featured version
"""
import os
import sys

# Use full-featured app with lightweight alternatives
from app_railway_full import app, initialize_railway_full

# Initialize components
if not initialize_railway_full():
    print("❌ Failed to initialize Railway full components")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)