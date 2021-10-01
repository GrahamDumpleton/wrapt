import os
import platform

import sys
import setuptools

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None


# # --- Detect if extensions should be disabled ------------------------------

wrapt_env = os.environ.get('WRAPT_INSTALL_EXTENSIONS')
if wrapt_env is None:
    wrapt_env = os.environ.get('WRAPT_EXTENSIONS')
if wrapt_env is not None:
    disable_extensions = wrapt_env.lower() == 'false'
    force_extensions = wrapt_env.lower() == 'true'
else:
    disable_extensions = False
    force_extensions = False
if platform.python_implementation() != "CPython":
    disable_extensions = True

# # --- stable ABI / limited API hacks ---------------------------------------
# Python < 3.9 is missing some features to build wheels with stable ABI

define_macros = []
cmdclass = {}

if sys.version_info >= (3, 9, 0) and platform.python_implementation() == "CPython":
    py_limited_api = True
    define_macros.append(("Py_LIMITED_API", "0x03090000"))

    if bdist_wheel is not None:
        class LimitedAPIWheel(bdist_wheel):
            def finalize_options(self):
                self.py_limited_api = "cp39"
                bdist_wheel.finalize_options(self)

        cmdclass["bdist_wheel"] = LimitedAPIWheel
else:
    py_limited_api = False


# --- C extension ------------------------------------------------------------

extensions = [
    setuptools.Extension(
        "wrapt._wrappers",
        sources=["src/wrapt/_wrappers.c"],
        optional=not force_extensions,
        py_limited_api=py_limited_api,
        define_macros=define_macros,
    )
]


# --- Setup ------------------------------------------------------------------

setuptools.setup(
    ext_modules=[] if disable_extensions else extensions,
    cmdclass=cmdclass
)
