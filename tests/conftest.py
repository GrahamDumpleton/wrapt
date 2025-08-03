import os
import re
import sys
import pathlib

import pytest

try:
    from pytest import File as FileCollector
except ImportError:
    from pytest.collect import File as FileCollector

version = tuple(sys.version_info[:2])


# Set MYPYPATH to the src directory relative to this conftest.py file. This
# allows mypy to find the source code for type checking.
_conftest_dir = pathlib.Path(__file__).parent
_src_dir = _conftest_dir.parent / "src"
os.environ["MYPYPATH"] = str(_src_dir)


class DummyCollector(FileCollector):
    def collect(self):
        return []


def construct_dummy(path, parent):
    if hasattr(DummyCollector, "from_parent"):
        item = DummyCollector.from_parent(parent, path=path)
        return item
    else:
        return DummyCollector(path, parent=parent)


def pytest_pycollect_makemodule(module_path, parent):
    basename = module_path.name

    # Handle Python 2/3 general cases
    if "_py2" in basename and version >= (3, 0):
        return construct_dummy(module_path, parent)
    if "_py3" in basename and version < (3, 0):
        return construct_dummy(module_path, parent)

    # Handle specific Python version cases using regex
    # Match patterns like "_py33", "_py34", "_py310", etc.
    version_match = re.search(r"_py(\d)(\d*)", basename)
    if version_match:
        major = int(version_match.group(1))
        minor_str = version_match.group(2)
        minor = int(minor_str) if minor_str else 0

        # Check if current version is less than the required version
        if version < (major, minor):
            return construct_dummy(module_path, parent)

    return None


# -----------------------------
# Custom mypy_*.py + .out tests
# -----------------------------


def run_custom_action(py_file: pathlib.Path) -> str:
    """
    Run mypy on the given file with the current interpreter's major.minor version
    and return the combined stdout/stderr output as text.
    """
    import subprocess
    import platform

    major, minor = version
    cmd = [
        "mypy",
        "--strict",
        "--show-error-codes",
        "--python-version",
        f"{major}.{minor}",
        str(py_file),
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        output = proc.stdout

        # On Windows, convert backslash paths to forward slashes for consistency
        # with .out files

        if platform.system() == "Windows":
            output = re.sub(r"\btests\\mypy\\", "tests/mypy/", output)

        return output
    except FileNotFoundError:
        return "mypy: command not found\n"


class MypyPairItem(pytest.Item):
    def __init__(self, name, parent, py_path: pathlib.Path, out_path: pathlib.Path):
        super().__init__(name, parent)
        self.py_path = py_path
        self.out_path = out_path

    def runtest(self):
        actual_output = run_custom_action(self.py_path)

        expected_output = self.out_path.read_text(encoding="utf-8")

        # Normalize line endings to avoid platform discrepancies
        if actual_output.replace("\r\n", "\n") != expected_output.replace("\r\n", "\n"):
            raise AssertionError(
                f"Output did not match expected for {self.py_path.name}\n"
                f"Expected (from {self.out_path.name}):\n{expected_output}\n"
                f"Actual:\n{actual_output}"
            )

    def reportinfo(self):
        return self.py_path, 0, f"mypy-pair: {self.py_path.name}"


class MypyPairCollector(pytest.File):
    """
    A collector that discovers mypy*.py files with corresponding .out files in
    the same directory and creates test items for them.
    """

    def collect(self):
        # Only run this custom collection on Python 3.9+
        if version < (3, 9):
            return

        path = pathlib.Path(str(self.fspath))
        # Only operate in a tests directory context
        if path.name != "conftest.py":
            return

        tests_dir = path.parent

        for py_file in sorted(tests_dir.glob("mypy/mypy_*.py")):
            out_file = py_file.with_suffix(".out")
            if out_file.exists():
                name = f"{py_file.stem}"
                # Create a test item for the pair
                yield MypyPairItem.from_parent(
                    parent=self, name=name, py_path=py_file, out_path=out_file
                )


def pytest_collect_file(file_path, parent):
    """
    Hook that allows adding our MypyPairCollector when pytest collects files.
    We attach the collector to tests/conftest.py so the discovery runs once per tests session.
    """
    # Guard early so we don't attach the collector on older Pythons
    if version < (3, 10):
        return

    # Newer pytest passes pathlib.Path-like objects; ensure we can get a string/Path
    try:
        p = pathlib.Path(str(file_path))
    except Exception:
        p = pathlib.Path(getattr(file_path, "strpath", str(file_path)))

    # Only hook our collector on the tests/conftest.py file to avoid multiple runs
    if p.name == "conftest.py" and p.parent.name == "tests":
        if hasattr(MypyPairCollector, "from_parent"):
            return MypyPairCollector.from_parent(parent, path=file_path)
        else:
            # Fallback for very old pytest versions
            return MypyPairCollector(file_path, parent=parent)
