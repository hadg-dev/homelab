#!/bin/zsh
set -e

echo "Cleaning homelab environment..."

rm -rf .venv
rm -f uv.lock

echo "Done."