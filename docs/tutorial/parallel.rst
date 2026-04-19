Parallel Runs
=============

pyOFTools works in parallel OpenFOAM runs without any changes to your Python code. Aggregation results are automatically reduced across MPI ranks, and CSV output is written only by the master process.

How it works
------------

When your solver runs under ``mpirun``, each MPI rank executes the Python post-processing on its local portion of the mesh. The C++ aggregation layer calls ``Foam::reduce()`` internally, so the final result is the global value across all ranks.

.. code-block:: bash

   # Serial --- works
   interFoam

   # Parallel --- same Python code, same results
   decomposePar
   mpirun -np 4 interFoam -parallel

Your ``postProcess.py`` file does not change between serial and parallel.

CSV output in parallel
----------------------

Only the master rank writes CSV files. This is handled automatically by ``TableWriter`` using ``Pstream.master()``. You do not need to add any rank checks in your Python code.

Checking parallel state
-----------------------

If you need to inspect the parallel environment (e.g., for debugging):

.. code-block:: python

   from pybFoam import Pstream

   Pstream.master()     # True on rank 0, False on others
   Pstream.parRun()     # True if running under mpirun
   Pstream.myProcNo()   # Current rank number
   Pstream.nProcs()     # Total number of ranks

Testing in parallel
-------------------

pyOFTools uses pytest with a ``parallel`` marker. Serial and parallel tests are run separately:

.. code-block:: bash

   # Serial tests
   pytest -m "not parallel"

   # Parallel tests (run pytest under mpirun)
   mpirun -np 2 --oversubscribe pytest -m parallel
