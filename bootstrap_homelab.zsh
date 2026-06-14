#!/bin/zsh

# First install multipass 10.15
# brew install --cask multipass
# multipass version
# Install k9s for cluster management
#echo "Installing k9s..."
#brew install derailed/k9s/k9s
#multipass exec k8s-ctrl -- sudo cat /etc/rancher/k3s/k3s.yaml \
#| sed "s/127.0.0.1/192.168.64.12/" \
#> ~/.kube/config

set -e

# Root homelab directory used throughout bootstrap.

# -----------------------------------------------------------------------------
# Ensure required local tooling is available
# -----------------------------------------------------------------------------

echo "Installing required tools..."

multipass version

if ! command -v brew >/dev/null; then
    echo "Homebrew missing."
    exit 1
fi

if ! command -v uv >/dev/null; then
    brew install uv
fi

if ! command -v tree >/dev/null; then
    brew install tree
fi

if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zshrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
fi

export PATH="$HOME/.local/bin:$PATH"

# -----------------------------------------------------------------------------
# Initialize git repository if needed
# -----------------------------------------------------------------------------

echo "Initializing git..."

if [ ! -d ".git" ]; then
    git init
    git config --global init.defaultBranch main

fi


echo "Creating gitignore..."
cat > .gitignore <<EOF
.venv/
__pycache__/
*.pyc
state.json
EOF

echo "Installing Python 3.13..."
uv python install 3.13

echo "Creating venv..."
rm -rf .venv
uv venv --python 3.13

source .venv/bin/activate

echo "Creating pyproject..."

if [ ! -f pyproject.toml ]; then
    uv init --no-readme
    rm -f main.py
fi

echo "Installing dependencies..."
uv add typer rich

tree .

echo "make bootstrap"
make bootstrap
echo "State after bootstrap:"
cat state.json