#!/bin/bash
set -e

echo "=== Tailscale Setup ==="

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

echo "=== Tailscale IP ==="
tailscale ip -4

echo ""
echo "上記のIPアドレスを学生に共有してください。"
echo "アクセスURL: http://$(tailscale ip -4):3000"
