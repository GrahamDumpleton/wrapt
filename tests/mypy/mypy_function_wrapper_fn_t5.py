"""
This example demonstrates the incorrect usage of the function_wrapper() function.

It covers the following cases:
- Wrapper as non callable object
- Wrapper as None object

Should fail mypy type checking for incorrect cases.
"""

from wrapt import function_wrapper


wrapper = function_wrapper("string")
wrapper = function_wrapper(None)
