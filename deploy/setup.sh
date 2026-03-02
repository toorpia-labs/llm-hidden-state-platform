#!/bin/bash
set -e

PROJECT_DIR="/opt/llm-hidden-state-platform"
VENV_DIR="$PROJECT_DIR/backend/.venv"

echo "=== LLM Hidden State Platform Setup ==="

# System dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv nodejs npm

# Clone repository
sudo mkdir -p /opt
sudo chown $USER:$USER /opt
git clone git@github.com:toorpia-labs/llm-hidden-state-platform.git $PROJECT_DIR
cd $PROJECT_DIR

# Backend: Python venv + dependencies
python3.11 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Frontend: Node.js dependencies + build
cd $PROJECT_DIR/frontend
npm install
npm run build

# Data directory
mkdir -p $PROJECT_DIR/data/jobs

# Environment file
cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env
echo ">>> .env を編集して必要な設定を行ってください"

# Install systemd services
sudo cp $PROJECT_DIR/deploy/llm-platform-backend.service /etc/systemd/system/
sudo cp $PROJECT_DIR/deploy/llm-platform-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable llm-platform-backend llm-platform-frontend

echo "=== Setup complete ==="
echo "Start services: sudo systemctl start llm-platform-backend llm-platform-frontend"
