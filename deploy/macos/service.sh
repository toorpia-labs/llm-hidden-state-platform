#!/bin/bash
# macOS service manager for LLM Hidden State Platform
# Usage: ./service.sh {start|stop|restart|status}

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/data/logs"
PID_DIR="$PROJECT_DIR/data/pids"

BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

ensure_dirs() {
    mkdir -p "$LOG_DIR" "$PID_DIR"
}

is_running() {
    local pidfile="$1"
    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
        rm -f "$pidfile"
    fi
    return 1
}

start_backend() {
    if pid=$(is_running "$BACKEND_PID"); then
        echo "  Already running (PID: $pid)"
        return 0
    fi

    cd "$PROJECT_DIR/backend"
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 127.0.0.1 --port 8001 \
        >> "$LOG_DIR/backend.log" 2>> "$LOG_DIR/backend.error.log" &
    echo $! > "$BACKEND_PID"
    echo "  Started (PID: $!)"
}

start_frontend() {
    if pid=$(is_running "$FRONTEND_PID"); then
        echo "  Already running (PID: $pid)"
        return 0
    fi

    cd "$PROJECT_DIR/frontend"
    nohup npm run dev \
        >> "$LOG_DIR/frontend.log" 2>> "$LOG_DIR/frontend.error.log" &
    echo $! > "$FRONTEND_PID"
    echo "  Started (PID: $!)"
}

stop_process() {
    local name="$1"
    local pidfile="$2"

    if pid=$(is_running "$pidfile"); then
        kill "$pid" 2>/dev/null
        # Wait up to 5 seconds for graceful shutdown
        for i in $(seq 1 10); do
            if ! kill -0 "$pid" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$pidfile"
        echo "  Stopped (was PID: $pid)"
    else
        echo "  Not running"
    fi
}

start_services() {
    ensure_dirs
    echo "Starting backend..."
    start_backend
    echo "Starting frontend..."
    start_frontend
    echo ""
    echo "Logs: $LOG_DIR/"
}

stop_services() {
    echo "Stopping backend..."
    stop_process "backend" "$BACKEND_PID"
    echo "Stopping frontend..."
    stop_process "frontend" "$FRONTEND_PID"
    # Clean up any orphaned child processes
    pkill -f "uvicorn app.main:app.*8001" 2>/dev/null || true
    pkill -f "next-router-worker" 2>/dev/null || true
}

restart_services() {
    stop_services
    sleep 1
    start_services
}

status_services() {
    echo "=== LLM Platform Service Status ==="
    echo ""

    echo "Backend (FastAPI :8001):"
    if pid=$(is_running "$BACKEND_PID"); then
        echo "  Running (PID: $pid)"
    else
        echo "  Not running"
    fi

    echo ""
    echo "Frontend (Next.js :3000):"
    if pid=$(is_running "$FRONTEND_PID"); then
        echo "  Running (PID: $pid)"
    else
        echo "  Not running"
    fi

    echo ""
    echo "Health check:"
    if curl -sf http://127.0.0.1:8001/health > /dev/null 2>&1; then
        echo "  Backend:  OK"
    else
        echo "  Backend:  UNREACHABLE"
    fi
    if curl -sf -o /dev/null http://127.0.0.1:3000 2>&1; then
        echo "  Frontend: OK"
    else
        echo "  Frontend: UNREACHABLE"
    fi

    echo ""
    echo "Logs: $LOG_DIR/"
}

case "${1:-}" in
    start)      start_services ;;
    stop)       stop_services ;;
    restart)    restart_services ;;
    status)     status_services ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
