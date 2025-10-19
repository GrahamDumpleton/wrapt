#!/usr/bin/env bash
set -e

# Install just
sudo apt-get update
sudo apt-get install -y just

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install mypy using uv
uv tool install mypy
