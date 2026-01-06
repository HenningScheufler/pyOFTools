"""Extract solver performance information from OpenFOAM solverPerformanceDict."""

from __future__ import annotations

from typing import Any, Optional

from pybFoam import fvMesh

from .datasets import AggregatedData, AggregatedDataSet


def _to_scalar(value: Any) -> float:
    """Convert residual value to scalar (handle vector/tensor by taking max component)."""
    return max(value[i] for i in range(len(value))) if hasattr(value, "__len__") else float(value)


def residual_dataset(mesh: fvMesh, time_value: Optional[float] = None) -> AggregatedDataSet:
    """
    Extract solver performance information from mesh including inner iterations.

    Args:
        mesh: OpenFOAM mesh object
        time_value: Optional time value (unused, kept for API consistency)

    Returns:
        AggregatedDataSet with solver performance for all fields in long format.
        Each inner iteration gets its own row with iteration index.

    Example:
        >>> mesh = pf.fvMesh(time)
        >>> perf_data = residual_dataset(mesh)
        >>> # Headers: ['solverPerformance', 'field', 'solver', 'metric', 'iteration']
    """
    solver_dict = mesh.solverPerformanceDict()
    field_names = solver_dict.toc()

    if not field_names or not field_names.list():
        return AggregatedDataSet(name="solverPerformance", values=[])

    aggregated_values = []
    lookup_methods = [
        solver_dict.lookupSolverPerformanceScalarList,
        solver_dict.lookupSolverPerformanceVectorList,
        solver_dict.lookupSolverPerformanceTensorList,
    ]

    for field_name_word in field_names.list():
        field_name = str(field_name_word)

        for lookup_method in lookup_methods:
            try:
                solver_perf_list = lookup_method(field_name)

                # Iterate through all solver performances (inner iterations)
                for iter_idx, solver_perf in enumerate(solver_perf_list):
                    solver_name = str(solver_perf.solverName())
                    init_res = _to_scalar(solver_perf.initialResidual())
                    final_res = _to_scalar(solver_perf.finalResidual())
                    n_iters = float(solver_perf.nIterations())

                    group_names = ["field", "solver", "metric", "iteration"]

                    for metric_name, value in [
                        ("init_res", init_res),
                        ("final_res", final_res),
                        ("nSolverIters", n_iters),
                    ]:
                        aggregated_values.append(
                            AggregatedData(
                                value=value,
                                group=[field_name, solver_name, metric_name, iter_idx],
                                group_name=group_names,
                            )
                        )
                break
            except Exception:
                continue

    return AggregatedDataSet(name="solverPerformance", values=aggregated_values)
