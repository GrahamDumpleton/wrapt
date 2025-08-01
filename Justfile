# Default recipe - show available recipes
default:
    just --list

# Create virtual environment with uv
venv:
    uv venv --python 3.13
    uv pip install pip  # Install pip for backward compatibility

# Install the package in development mode
install: venv clear-cache
    uv pip install -e .

# Install from local source distribution (for testing)
install-local: package clear-cache
    uv pip install dist/wrapt-*.tar.gz

# Install from local source distribution with verbose output
install-local-verbose: package clear-cache
    uv pip install -v dist/wrapt-*.tar.gz

# Create source distribution package
package: venv
    uv run python setup.py sdist

# Clear pip cache for wrapt to avoid conflicts with local development
clear-cache:
    uv cache clean wrapt || true
    uv cache clean || true

# Release: clean, package, and upload to PyPI
release:
    echo "ERROR: Direct releases are no longer supported from this Justfile."
    echo "Release packages are built by GitHub Actions."
    echo "Push a tag to trigger the build workflow."
    exit 1

# Release to Test PyPI
release-test: clean package
    uv publish --index-url https://test.pypi.org/simple/ dist/*

# Remove coverage files
mostlyclean:
    rm -rf .coverage.*
    rm -rf src/wrapt/_wrappers.*.so
    rm -rf .pytest_cache
    rm -rf .tox .venv

# Clean build artifacts, coverage files, and virtual environment
clean: mostlyclean clear-cache
    rm -rf build dist src/wrapt.egg-info

# Run tests with tox
test-tox:
    tox --skip-missing-interpreters

# Run tests with uv (modern alternative)
test:
    just test-version 3.8
    just test-version 3.9
    just test-version 3.10
    just test-version 3.11
    just test-version 3.12
    just test-version 3.13
    just test-version 3.14

# Run mypy type checking for all supported Python versions
test-mypy:
    just test-mypy-version 3.8
    just test-mypy-version 3.9
    just test-mypy-version 3.10
    just test-mypy-version 3.11
    just test-mypy-version 3.12
    just test-mypy-version 3.13
    just test-mypy-version 3.14

# Run tests with uv for a specific Python version
test-version version:
    #!/usr/bin/env bash
    set -euo pipefail
    
    echo "=== Testing Python {{version}} - without C extensions ==="
    rm -rf .venv-test-tmp
    uv venv .venv-test-tmp --python {{version}}
    source .venv-test-tmp/bin/activate
    uv pip install pytest
    WRAPT_INSTALL_EXTENSIONS=false uv pip install -e .
    pytest
    deactivate
    
    echo "=== Testing Python {{version}} - with C extensions ==="
    rm -rf .venv-test-tmp
    uv venv .venv-test-tmp --python {{version}}
    source .venv-test-tmp/bin/activate
    uv pip install pytest
    WRAPT_INSTALL_EXTENSIONS=true uv pip install -e .
    pytest
    deactivate
    
    echo "=== Testing Python {{version}} - with C extensions disabled at runtime ==="
    rm -rf .venv-test-tmp
    uv venv .venv-test-tmp --python {{version}}
    source .venv-test-tmp/bin/activate
    uv pip install pytest
    WRAPT_INSTALL_EXTENSIONS=true uv pip install -e .
    WRAPT_DISABLE_EXTENSIONS=true pytest
    deactivate
    
    rm -rf .venv-test-tmp
    echo "All test variants completed for Python {{version}}"

# Run mypy type checking for a specific Python version
test-mypy-version version:
    echo "=== Running mypy type checking with Python {{version}} ==="
    uv run --python {{version}} mypy src/wrapt

# Install development dependencies with uv
dev-install: venv
    uv sync

# Run tests using pip-installed pytest (backward compatibility check)
test-pip: venv
    source .venv/bin/activate && pip install pytest && pip install -e . && pytest

# Check if virtual environment exists
venv-check:
    if [ ! -d ".venv" ]; then echo "Virtual environment not found. Run 'just venv' first."; exit 1; fi

# Activate virtual environment (for interactive use)
shell: venv
    echo "Activating virtual environment..."
    echo "Run: source .venv/bin/activate"

# Show virtual environment info
venv-info: venv-check
    source .venv/bin/activate && python --version && pip --version
