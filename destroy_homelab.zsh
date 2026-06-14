#!/bin/zsh

set -e

# Root homelab path used for cleanup.
HOMELAB_DIR="$HOME/homelab"

# -----------------------------------------------------------------------------
# Multipass instance cleanup
# -----------------------------------------------------------------------------

echo "Cleaning Multipass instances..."

multipass delete k8s-ctrl --purge 2>/dev/null || true
multipass delete k8s-worker-1 --purge 2>/dev/null || true

# Optional future worker instance cleanup.
multipass delete k8s-worker-2 --purge 2>/dev/null || true

multipass purge 2>/dev/null || true

echo "Multipass cleanup complete."

# -----------------------------------------------------------------------------
# Homelab directory cleanup
# -----------------------------------------------------------------------------

echo "Destroying homelab resources..."

rm .python-version 2>/dev/null || true
rm -rf .venv 2>/dev/null || true
rm -f uv.lock 2>/dev/null || true
rm uv.lock 2>/dev/null || true
rm state.json 2>/dev/null || true
rm pyproject.toml 2>/dev/null || true
rm .gitignore 2>/dev/null || true


if [ -d "$HOMELAB_DIR" ]; then
    rm -rf "$HOMELAB_DIR"
    echo "Removed $HOMELAB_DIR"
else
    echo "Homelab directory not found."
fi

echo "Cleanup complete."