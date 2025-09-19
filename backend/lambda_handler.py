"""
AWS Lambda handler for FastAPI application
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from mangum import Mangum
from app.main import app

# Create the Lambda handler
handler = Mangum(
    app,
    lifespan="off"  # Disable lifespan events for Lambda
)
