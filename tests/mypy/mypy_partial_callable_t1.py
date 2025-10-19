"""
This example demonstrates the correct usage of the partial().
"""

from wrapt import PartialCallableObjectProxy, partial


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


# Using partial to create a new function with default arguments
partial_function = partial(function, y="custom")

# Calling the partially applied function
partial_function_result = partial_function(42)

# Using partial with no arguments (FAIL)
partial_function_no_args = partial()

# Using partial with incorrect arguments (FAIL)
partial_function_incorrect = partial(None)

# Using PartialCallableObjectProxy to create a new function with default arguments
partial_object = PartialCallableObjectProxy(function, y="custom")

# Calling the partially applied function
partial_object = partial_object(42)

# Using PartialCallableObjectProxy with no arguments (FAIL)
partial_object_no_args = PartialCallableObjectProxy()

# Using PartialCallableObjectProxy with incorrect arguments (FAIL)
partial_object_incorrect = PartialCallableObjectProxy(None)
