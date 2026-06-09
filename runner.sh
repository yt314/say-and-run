#!/bin/bash
# Simple runner script for the CLI Command Generator

echo "🔧 CLI Command Generator - Prompt Engineering"
echo "=============================================="
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable not set"
    echo ""
    echo "Please set it before running:"
    echo "  export OPENAI_API_KEY='sk-your-key-here'"
    exit 1
fi

echo "✅ OPENAI_API_KEY is set"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo ""
    echo "Install uv from: https://docs.astral.sh/uv/"
    exit 1
fi

echo "✅ uv is installed"
echo ""

# Sync dependencies
echo "📦 Syncing dependencies..."
uv sync

if [ $? -ne 0 ]; then
    echo "❌ Failed to sync dependencies"
    exit 1
fi

echo ""
echo "✅ Dependencies synced"
echo ""

# Run the app
echo "🚀 Starting Gradio app..."
echo "📡 Access it at: http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uv run python main.py
