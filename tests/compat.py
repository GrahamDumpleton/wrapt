import sys

PYXY = tuple(sys.version_info[:2])

try:
    from inspect import getfullargspec
except ImportError:
    from inspect import getargspec as getfullargspec
