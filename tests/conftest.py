import sys

import pytest

version = tuple(sys.version_info[:2])

class DummyCollector(pytest.collect.File):
    def collect(self):
        return []

def pytest_pycollect_makemodule(path, parent):
    if '_py33' in path.basename and version < (3, 3):
        return DummyCollector(path, parent=parent)
    if '_py3' in path.basename and version < (3, 0):
        return DummyCollector(path, parent=parent)
    if '_py2' in path.basename and version >= (3, 0):
        return DummyCollector(path, parent=parent)
