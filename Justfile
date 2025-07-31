# Default recipe - show available recipes
default:
    just --list

# Install the package
install:
    pip install -U .

# Create source distribution package
package:
    python setup.py sdist

# Release: clean, package, and upload to PyPI
release: clean package
    twine upload dist/*

# Remove coverage files
mostlyclean:
    rm -rf .coverage.*

# Clean build artifacts and coverage files
clean: mostlyclean
    rm -rf build dist src/wrapt.egg-info .tox

# Run tests with tox
test-tox:
    tox --skip-missing-interpreters

# Run tests with uv (modern alternative)
test:
    uv run --python 3.8 pytest
    uv run --python 3.9 pytest
    uv run --python 3.10 pytest
    uv run --python 3.11 pytest
    uv run --python 3.12 pytest
    uv run --python 3.13 pytest
    uv run --python 3.14 pytest

# Run tests with uv for a specific Python version
test-version version:
    uv run --python {{version}} pytest

# Install development dependencies with uv
dev-install:
    uv sync
