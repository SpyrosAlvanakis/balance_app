#!/bin/sh
set -eu

# On Railway, secrets aren't checked into git. If the SECRETS_TOML env var is
# set, materialize it as .streamlit/secrets.toml before launching Streamlit.
mkdir -p .streamlit
if [ -n "${SECRETS_TOML:-}" ]; then
  printf '%s' "$SECRETS_TOML" > .streamlit/secrets.toml
fi

exec python -m streamlit run home.py --server.address 0.0.0.0 --server.port "${PORT:-8501}" --server.headless true
