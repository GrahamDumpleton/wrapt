import sys

from pytest import File as FileCollector

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
    if '_py39' in path.basename and version < (3, 9):
        return construct_dummy(path, parent)
    if '_py310' in path.basename and version < (3, 10):
        return construct_dummy(path, parent)
    if '_py311' in path.basename and version < (3, 11):
        return construct_dummy(path, parent)
    if '_py312' in path.basename and version < (3, 12):
        return construct_dummy(path, parent)
    if '_py3' in path.basename and version < (3, 0):
        return construct_dummy(path, parent)
    if '_py2' in path.basename and version >= (3, 0):
        return construct_dummy(path, parent)
