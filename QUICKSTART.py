"""
Quick Start Guide

Step 1: Install dependencies
Step 2: Set environment variables
Step 3: Run proof-of-concept demo
"""

# Installation instructions
INSTALL_INSTRUCTIONS = """
# 1. Create virtual environment (Windows)
python -m venv venv
venv\\Scripts\\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
# Copy .env.example to .env and fill in your API keys:
#   - ANTHROPIC_API_KEY=your_key_here

# 4. Run the demo
python examples/poc_demo.py
"""

print(INSTALL_INSTRUCTIONS)
