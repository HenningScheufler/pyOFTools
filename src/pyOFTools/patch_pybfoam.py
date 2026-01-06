"""
Utility to patch pybFoam to disable FPE trapping after initialization.

This patches the pybFoam.Time and pybFoam.fvMesh classes to automatically
disable floating point exception trapping after OpenFOAM initialization,
preventing crashes when NumPy/pandas are used.

Usage:
    >>> import pyOFTools.patch_pybfoam  # Import once at the start
    >>> import pybFoam  # Now safe to use
"""

import ctypes


def disable_fpe():
    """Disable floating point exception trapping at C library level"""
    try:
        libc = ctypes.CDLL(None)
        # FE_ALL_EXCEPT = 0x3f
        libc.fedisableexcept(0x3F)
    except (OSError, AttributeError):
        pass


def patch_pybfoam():
    """Monkey-patch pybFoam classes to disable FPE after initialization"""
    try:
        import pybFoam

        # Patch Time class
        if hasattr(pybFoam, "Time"):
            original_time_init = pybFoam.Time.__init__

            def time_init_wrapper(self, *args, **kwargs):
                result = original_time_init(self, *args, **kwargs)
                disable_fpe()
                return result

            pybFoam.Time.__init__ = time_init_wrapper

        # Patch fvMesh class
        if hasattr(pybFoam, "fvMesh"):
            original_mesh_init = pybFoam.fvMesh.__init__

            def mesh_init_wrapper(self, *args, **kwargs):
                result = original_mesh_init(self, *args, **kwargs)
                disable_fpe()
                return result

            pybFoam.fvMesh.__init__ = mesh_init_wrapper

    except ImportError:
        # pybFoam not installed, skip patching
        pass
    except Exception as e:
        print(f"Warning: Failed to patch pybFoam: {e}")


# Auto-patch when this module is imported
patch_pybfoam()
