import sys

try:
    from pytest import File as FileCollector
except ImportError:
    from pytest.collect import File as FileCollector

version = tuple(sys.version_info[:2])

class DummyCollector(FileCollector):
    def collect(self):
        return []

def construct_dummy(path, parent):
    if hasattr(DummyCollector, "from_parent"):
        item = DummyCollector.from_parent(parent, fspath=path)
        return item
    else:
        return DummyCollector(path, parent=parent)

def pytest_pycollect_makemodule(path, parent):
    if '_py33' in path.basename and version < (3, 3):
        return construct_dummy(path, parent)
    if '_py37' in path.basename and version < (3, 7):
        return construct_dummy(path, parent)
    if '_py3' in path.basename and version < (3, 0):
        return construct_dummy(path, parent)
    if '_py2' in path.basename and version >= (3, 0):
        return construct_dummy(path, parent)
