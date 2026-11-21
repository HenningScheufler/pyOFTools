"""
Utility to patch pybFoam to disable FPE trapping after initialization.

OpenFOAM enables floating point traps while parsing an ``argList``. In a Python
process those traps stay active and can crash NumPy, pandas or CPython itself.
This patches ``pybFoam.argList`` and ``pybFoam.selectTimes``, the two bindings
that construct an ``argList``, to disable the traps again before returning.

nanobind constructs instances without looking up a Python-level ``__init__``,
so assigning to ``argList.__init__`` has no effect. A subclass is used instead.

Import this module before binding ``argList`` or ``selectTimes`` to a local name.

Usage:
    >>> import pyOFTools.patch_pybfoam  # Import once at the start
    >>> import pybFoam  # Now safe to use
"""

import ctypes
from typing import Any


def disable_fpe() -> None:
    """Disable floating point exception trapping at C library level"""
    try:
        libc = ctypes.CDLL(None)
        # FE_ALL_EXCEPT = 0x3f
        libc.fedisableexcept(0x3F)
    except (OSError, AttributeError):
        pass


def patch_pybfoam() -> None:
    """Replace the pybFoam entry points that enable FPE trapping"""
    try:
        import pybFoam
        from pybFoam import pybFoam_core

        original_select_times = pybFoam_core.selectTimes

        class argList(pybFoam_core.argList):  # type: ignore[misc, name-defined, unused-ignore]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                disable_fpe()

        def selectTimes(*args: Any, **kwargs: Any) -> Any:
            try:
                return original_select_times(*args, **kwargs)
            finally:
                disable_fpe()

        for module in (pybFoam, pybFoam_core):
            setattr(module, "argList", argList)
            setattr(module, "selectTimes", selectTimes)

    except ImportError:
        # pybFoam not installed, skip patching
        pass
    except Exception as e:
        print(f"Warning: Failed to patch pybFoam: {e}")


# Auto-patch when this module is imported
patch_pybfoam()
