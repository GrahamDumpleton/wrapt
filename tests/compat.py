import sys

PY3 = sys.version_info[0] >= 3

PYXY = tuple(sys.version_info[:2])

try:
    from inspect import getfullargspec
except ImportError:
    from inspect import getargspec as getfullargspec
