import sys

import pytest

version = tuple(sys.version_info[:2])

class DummyCollector(pytest.File):
    def collect(self):
        return []

def pytest_pycollect_makemodule(path, parent):
    if version < (3, 0):
        if '_py27' in path.basename:
            return DummyCollector(path, parent=parent)
    else:
        if '_py33' in path.basename and version < (3, 3):
            return DummyCollector.from_parent(parent, fspath=path)
        if '_py37' in path.basename and version < (3, 7):
            return DummyCollector.from_parent(parent, fspath=path)
        if '_py3' in path.basename and version < (3, 0):
            return DummyCollector.from_parent(parent, fspath=path)
        if '_py2' in path.basename and version >= (3, 0):
            return DummyCollector.from_parent(parent, fspath=path)
