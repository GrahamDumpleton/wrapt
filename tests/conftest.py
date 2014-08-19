import pytest

from compat import PY2, PY3

class DummyCollector(pytest.collect.File):
    def collect(self):
         return []

def pytest_pycollect_makemodule(path, parent):
    if "py3" in path.basename and not PY3:
        return DummyCollector(path, parent=parent)
    if "py2" in path.basename and not PY2:
        return DummyCollector(path, parent=parent)
