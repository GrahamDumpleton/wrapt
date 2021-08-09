import os
import platform
import setuptools


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

# --- C extension ------------------------------------------------------------

extensions = [
    setuptools.Extension(
        "wrapt._wrappers",
        sources=["src/wrapt/_wrappers.c"],
        optional=not force_extensions,
    )
]


# --- Setup ------------------------------------------------------------------

setuptools.setup(
    ext_modules=[] if disable_extensions else extensions
)
