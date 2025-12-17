#!/bin/bash
# PhazeOS AI Pod Setup (Pure Bash)
# Installs Ollama and configures local models without Python scripts.

echo "🤖 INITIALIZING AI POD (Bash Protocol)..."

# 1. Install Ollama (Self-Hosted)
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed."
fi

# 2. Enable Service
sudo systemctl enable --now ollama

# 3. Pull Models (Background)
# We pull a small model first to verify connectivity
echo "Pulling 'mistral' model (optimized for local use)..."
ollama pull mistral

echo "✅ AI Pod Ready."
echo "Run 'ollama run mistral' to interact."
