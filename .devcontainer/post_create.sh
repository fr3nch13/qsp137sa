#!/usr/bin/env bash
set -euo pipefail

# Runs when the devcontainer is created.

echo "Running post-create script..."

uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
echo "Post-create script completed."
