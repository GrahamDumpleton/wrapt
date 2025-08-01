# Testing Guide

This document explains how to run tests for the wrapt project and the conventions used for Python version-specific test files.

## Test Directory Structure

The `tests/` directory contains all test files for the wrapt project. Test files follow these conventions:

- **Standard test files**: `test_*.py` - These run on all supported Python versions
- **Python version-specific test files**: `test_*_pyXX.py` - These only run on specific Python versions or later

## Python Version-Specific Test Files

The project uses a special naming convention to ensure certain tests only run on appropriate Python versions. This is handled automatically by the `conftest.py` configuration.

### Naming Convention

Test files can include version suffixes to indicate minimum Python version requirements:

- `test_name_py3.py` - Runs only on Python 3.x (skipped on Python 2.x)
- `test_name_py2.py` - Runs only on Python 2.x (skipped on Python 3.x)
- `test_name_py36.py` - Runs only on Python 3.6 and later
- `test_name_py37.py` - Runs only on Python 3.7 and later
- `test_name_py38.py` - Runs only on Python 3.8 and later

### Examples in the Codebase

- `test_formatargspec_py35.py` - Tests features that require Python 3.5+ (like type annotations)
- `test_formatargspec_py38.py` - Tests features that require Python 3.8+ (like positional-only parameters)
- `test_class_py37.py` - Tests class-related features that require Python 3.7+
- `test_descriptors_py36.py` - Tests descriptor features that require Python 3.6+
- `test_inheritance_py37.py` - Tests inheritance features that require Python 3.7+
- `test_adapter_py33.py` - Tests adapter features that require Python 3.3+ (keyword-only arguments)

### How It Works

The `conftest.py` file contains a `pytest_pycollect_makemodule` hook that:

1. Parses the filename for version patterns using regex: `_py(\d)(\d*)`
2. Compares the detected version requirement with the current Python version
3. Returns a dummy collector (skips the test) if the current version is too old
4. Allows normal test collection if the version requirement is met

## Running Tests

The project provides several ways to run tests using the `just` command runner.

### Available Test Commands

#### Run All Tests
```bash
just test
```
This runs the complete test suite across all supported Python versions (3.8-3.14). For each version, it tests three scenarios:
1. Without C extensions
2. With C extensions
3. With C extensions disabled at runtime

#### Test Specific Python Version
```bash
just test-version 3.13
```
Replace `3.13` with any supported Python version (3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14).

#### Legacy Test Runner (using tox)
```bash
just test-tox
```
Runs tests using the traditional tox configuration.

#### Simple Test Run (backward compatibility)
```bash
just test-pip
```
Runs tests using pip-installed pytest in the main virtual environment.

#### Type Checking with mypy
```bash
just test-mypy
```
Runs mypy type checking across all supported Python versions (3.8-3.14).

```bash
just test-mypy-version 3.13
```
Runs mypy type checking for a specific Python version. Replace `3.13` with any supported version.

### Test Variants

Each `test-version` run includes three important test scenarios:

1. **Without C Extensions** (`WRAPT_INSTALL_EXTENSIONS=false`)
   - Tests the pure Python implementation
   - Ensures the fallback code works correctly

2. **With C Extensions** (`WRAPT_INSTALL_EXTENSIONS=true`)
   - Tests the optimized C implementation
   - Verifies performance-critical paths

3. **C Extensions Disabled at Runtime** (`WRAPT_DISABLE_EXTENSIONS=true`)
   - Tests the ability to disable C extensions after installation
   - Useful for debugging and compatibility testing

### Environment Variables

- `WRAPT_INSTALL_EXTENSIONS=true/false` - Controls whether C extensions are built during installation
- `WRAPT_DISABLE_EXTENSIONS=true/false` - Controls whether C extensions are used at runtime

## Development Workflow

### Testing During Development

For quick testing during development, you can:

1. Run all tests against all Python versions:
   ```bash
   just test
   ```

2. Test a specific Python version you're working with:
   ```bash
   just test-version 3.11
   ```

3. Run legacy tests if needed:
   ```bash
   just test-tox
   ```

4. Run type checking across all Python versions:
   ```bash
   just test-mypy
   ```

5. Run type checking for a specific Python version:
   ```bash
   just test-mypy-version 3.11
   ```

### Adding New Tests

When adding new test files:

1. Use the standard `test_*.py` naming convention for general tests
2. Use the `test_*_pyXX.py` convention if your test requires features from a specific Python version
3. The version detection is automatic - no additional configuration needed

### Test Dependencies

Test dependencies are managed in `pyproject.toml`. The main requirements are:
- `pytest` - For running unit tests
- `mypy` - For type checking and static analysis

If running `tox`, it is assumed that is installed as a tool using `uv tool install` command (or any other available method) and available in your `PATH`.

## Continuous Integration

The project uses GitHub Actions for automated testing. Tests are triggered on:
- Release tags
- Pull requests
- Workflow dispatch

The CI system runs the full test suite across all supported Python versions and platforms.
