#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/backend/.venv"

echo "=== LLM Hidden State Platform Setup ==="

OS="$(uname -s)"

# Backend: Python venv + dependencies
echo "Setting up backend..."
if [ "$OS" = "Darwin" ]; then
    PYTHON="${PYTHON:-/opt/homebrew/bin/python3.13}"
    REQUIREMENTS="requirements.txt"
else
    PYTHON="${PYTHON:-python3.11}"
    REQUIREMENTS="requirements-cuda.txt"

    # Install system dependencies (Ubuntu/Debian)
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3.11 python3.11-venv nodejs npm
    fi
fi

"$PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/backend/$REQUIREMENTS"

# Frontend: Node.js dependencies + build
echo "Setting up frontend..."
cd "$PROJECT_DIR/frontend"
npm install
npm run build

# Data directory
mkdir -p "$PROJECT_DIR/data/jobs" "$PROJECT_DIR/data/logs" "$PROJECT_DIR/data/pids"

# Environment file
if [ ! -f "$PROJECT_DIR/.env" ] && [ -f "$PROJECT_DIR/.env.example" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo ">>> .env を編集して必要な設定を行ってください"
fi

# Ubuntu: install systemd services
if [ "$OS" = "Linux" ] && command -v systemctl &>/dev/null; then
    sudo cp "$PROJECT_DIR/deploy/llm-platform-backend.service" /etc/systemd/system/
    sudo cp "$PROJECT_DIR/deploy/llm-platform-frontend.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable llm-platform-backend llm-platform-frontend
fi

echo "=== Setup complete ==="
if [ "$OS" = "Darwin" ]; then
    echo "Start: deploy/macos/service.sh start"
else
    echo "Start: sudo systemctl start llm-platform-backend llm-platform-frontend"
fi
