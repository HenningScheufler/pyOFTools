"""Global reductions over all MPI processes, provided by ``pybFoam.parallel``.

Keep the namespace so these stay distinct from the local ``sum``, ``min`` and
``max`` of Python and NumPy::

    from pyOFTools import parallel

    mass_flow = parallel.sum(phi)
"""

from pybFoam.parallel import max, min, sum, weighted_average

__all__ = ["max", "min", "sum", "weighted_average"]
