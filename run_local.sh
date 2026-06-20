#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed. Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if [ ! -f .streamlit/secrets.toml ]; then
    echo "Missing .streamlit/secrets.toml."
    echo "Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and fill in"
    echo "credentials for your DEV/TEST Google Sheet (not production)."
    exit 1
fi

uv sync
uv run streamlit run home.py
