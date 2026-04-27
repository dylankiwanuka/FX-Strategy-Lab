#!/bin/bash
# One-command setup for FX Strategy Lab.
# Creates a virtual environment, installs dependencies, and prints the run command.

set -e

echo "Setting up FX Strategy Lab..."

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "Setup complete."
echo "To run the app:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"
