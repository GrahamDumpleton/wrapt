# Testing Guide

This document explains how to run tests for the wrapt project and the conventions used for Python version-specific test files.

## Test Directory Structure

The `tests/core/` directory contains all test files for the wrapt project. Test files follow these conventions:

- **Standard test files**: `test_*.py` - These run on all supported Python versions
- **Python version-specific test files**: `test_*_pyXX.py` - These only run on specific Python versions or later

## Python Version-Specific Test Files

The project uses a special naming convention to ensure certain tests only run on appropriate Python versions. This is handled automatically by the `tests/conftest.py` configuration.

### Naming Convention

Test files can include version suffixes to indicate minimum Python version requirements:

- `test_name_py3.py` - Runs only on Python 3.x (skipped on Python 2.x)
- `test_name_py2.py` - Runs only on Python 2.x (skipped on Python 3.x)
- `test_name_py36.py` - Runs only on Python 3.6 and later
- `test_name_py37.py` - Runs only on Python 3.7 and later
- `test_name_py38.py` - Runs only on Python 3.8 and later

### Examples in the Codebase

- `test_class_py37.py` - Tests class-related features that require Python 3.7+
- `test_descriptors_py36.py` - Tests descriptor features that require Python 3.6+
- `test_inheritance_py37.py` - Tests inheritance features that require Python 3.7+
- `test_adapter_py33.py` - Tests adapter features that require Python 3.3+ (keyword-only arguments)

### How It Works

The `tests/conftest.py` file contains a `pytest_pycollect_makemodule` hook that:

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

## Mypy Type Checking Tests

The project includes custom pytest handlers for testing mypy type checking behavior. These tests ensure that the wrapt library's type annotations work correctly and produce expected mypy error messages.

### Test File Convention

Mypy tests follow a specific naming pattern in the `tests/mypy/` directory:

- **Test files**: `mypy_*.py` - Python files containing code to be type-checked
- **Expected output files**: `mypy_*.out` - Files containing the expected mypy output

### How Mypy Tests Work

The custom test handler in `conftest.py` automatically discovers pairs of `mypy_*.py` and `mypy_*.out` files and:

1. Runs `mypy --show-error-codes --python-version X.Y` on the `.py` file
2. Compares the actual output with the expected output in the `.out` file
3. Fails the test if the outputs don't match

These tests only run on Python 3.9+ to ensure consistent mypy behavior.

### Creating New Mypy Tests

To create a new mypy test case:

1. **Create the test file**: Write a Python file with the code you want to type-check:
   ```bash
   # Create tests/mypy/mypy_your_test_name.py
   ```

2. **Review output from test**: Review the test output to ensure it contains the expected error messages and type information:
   ```bash
   just view-mypy-test mypy_your_test_name
   ```

3. **Save the expected output**: Run mypy to capture the expected output, by running:
   ```bash
   just save-mypy-test mypy_your_test_name
   ```

3. **Verify the output**: Check the output from running the test against expected output, by running: 
   ```bash
   just check-mypy-test mypy_your_test_name
   ```

4. **Run the test**: The test will automatically be discovered and run with pytest:
   ```bash
   uv run pytest tests/ -k mypy_your_test_name
   ```

### Example

The existing `mypy_function_wrapper.py` test demonstrates type checking for `FunctionWrapper`:

```python
from wrapt import FunctionWrapper

def f(a: bool, b: str) -> int:
    return 1

def standard_wrapper(wrapped, instance, *args, **kwargs):
    pass

f1 = FunctionWrapper(f, standard_wrapper)
reveal_type(f1)  # Should reveal the original function's type

result1a: int = f1(True, "test")     # Valid usage
result1b: str = f1(1, None)         # Invalid usage - should error
```

The corresponding `mypy_function_wrapper.out` file contains the expected mypy output, including:
- Type revelation notes
- Assignment errors
- Argument type errors
- Error codes for each issue

This approach ensures that the wrapt library's type annotations behave consistently and provide helpful error messages to users.

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

1. **Standard unit tests**: Use the `test_*.py` naming convention for general tests
2. **Version-specific tests**: Use the `test_*_pyXX.py` convention if your test requires features from a specific Python version
3. **Mypy type tests**: Use the `mypy_*.py` naming convention for type checking tests (see the Mypy Type Checking Tests section above)
4. The version detection is automatic - no additional configuration needed

### Test Dependencies

Test dependencies are managed in `pyproject.toml`. The main requirements are:
- `pytest` - For running unit tests

If running `tox` or `mypy` tests, it is assumed that these are installed as a tool using `uv tool install` command (or any other available method) and available in your `PATH`.

## Continuous Integration

The project uses GitHub Actions for automated testing. Tests are triggered on:
- Release tags
- Pull requests
- Workflow dispatch

The CI system runs the full test suite across all supported Python versions and platforms.
