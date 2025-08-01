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
test: dev-install
    uv run --python 3.8 pytest
    uv run --python 3.9 pytest
    uv run --python 3.10 pytest
    uv run --python 3.11 pytest
    uv run --python 3.12 pytest
    uv run --python 3.13 pytest
    uv run --python 3.14 pytest

# Run tests with uv for a specific Python version
test-version version: dev-install
    uv run --python {{version}} pytest

# Install development dependencies with uv
dev-install: venv
    uv sync

# Run tests using pip-installed pytest (backward compatibility check)
test-pip: venv
    source .venv/bin/activate && pip install pytest && pytest

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
