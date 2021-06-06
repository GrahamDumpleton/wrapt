import os
import setuptools
import sys


# # --- Detect if extensions should be disabled ------------------------------

wrapt_env = os.environ.get('WRAPT_INSTALL_EXTENSIONS')
if wrapt_env is None:
    wrapt_env = os.environ.get('WRAPT_EXTENSIONS')
if wrapt_env is not None:
    disable_extensions = wrapt_env.lower() == 'false'
else:
    disable_extensions = False
if sys.implementation.name != "cpython":
    disable_extensions = True

# --- C extension ------------------------------------------------------------

extensions = [
    setuptools.Extension(
        "wrapt._wrappers",
        sources=[ os.path.realpath(os.path.join(__file__, "..", "src", "wrapt", "_wrappers.c"))],
        optional=True,
    )
]


# --- Setup ------------------------------------------------------------------

setuptools.setup(
    ext_modules=[] if disable_extensions else extensions
)
