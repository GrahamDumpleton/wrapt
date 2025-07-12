import sys
import re

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
    basename = path.basename
    
    # Handle Python 2/3 general cases
    if "_py2" in basename and version >= (3, 0):
        return construct_dummy(path, parent)
    if "_py3" in basename and version < (3, 0):
        return construct_dummy(path, parent)
    
    # Handle specific Python version cases using regex
    # Match patterns like "_py33", "_py34", "_py310", etc.
    version_match = re.search(r'_py(\d+)(\d*)', basename)
    if version_match:
        major = int(version_match.group(1))
        minor_str = version_match.group(2)
        minor = int(minor_str) if minor_str else 0
        
        # Check if current version is less than the required version
        if version < (major, minor):
            return construct_dummy(path, parent)
    
    return None
