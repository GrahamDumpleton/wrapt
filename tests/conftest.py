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
    if '_py34' in path.basename and version < (3, 4):
        return construct_dummy(path, parent)
    if '_py35' in path.basename and version < (3, 5):
        return construct_dummy(path, parent)
    if '_py36' in path.basename and version < (3, 6):
        return construct_dummy(path, parent)
    if '_py37' in path.basename and version < (3, 7):
        return construct_dummy(path, parent)
    if '_py38' in path.basename and version < (3, 8):
        return construct_dummy(path, parent)
    if '_py39' in path.basename and version < (3, 9):
        return construct_dummy(path, parent)
    if '_py310' in path.basename and version < (3, 10):
        return construct_dummy(path, parent)
    if '_py3' in path.basename and version < (3, 0):
        return construct_dummy(path, parent)
    if '_py2' in path.basename and version >= (3, 0):
        return construct_dummy(path, parent)
