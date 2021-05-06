import sys

import pytest

version = tuple(sys.version_info[:2])


class DummyCollector(pytest.File):
    def collect(self):
        return []


def collect(path, parent):
    """Helper function deal with differences between Python 2 and 3."""
    if version[0] == 2:
        return DummyCollector(path, parent=parent)
    else:
        return DummyCollector.from_parent(parent, fspath=path)


def pytest_pycollect_makemodule(path, parent):
    """Use a dummy collector to collect version-incompatible test files."""
    if '_py33' in path.basename and version < (3, 3):
        return collect(path, parent)
    if '_py37' in path.basename and version < (3, 7):
        return collect(path, parent)
    if '_py3' in path.basename and version < (3, 0):
        return collect(path, parent)
    if '_py2' in path.basename and version >= (3, 0):
        return collect(path, parent)
