"""Helpers for the example cases shipped under ``examples/``."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

__all__ = ["clone_example", "examples_root"]


def examples_root() -> Path:
    """Path to the repo's ``examples/`` directory."""
    pkg_candidate = Path(__file__).resolve().parents[2] / "examples"
    if pkg_candidate.is_dir():
        return pkg_candidate

    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / "examples"
        if candidate.is_dir():
            return candidate
        if parent.name == "examples" and parent.is_dir():
            return parent

    raise FileNotFoundError("examples/ not found — run from a repo checkout or `pip install -e .`.")


def clone_example(name: str, *, prefix: str = "pyoftools_") -> Path:
    """Copy ``examples/<name>/`` to a tmp dir, restoring ``0.orig`` → ``0``."""
    baseline = (examples_root() / name).resolve()
    if not baseline.is_dir():
        raise FileNotFoundError(f"No example case at {baseline}")

    target = Path(tempfile.mkdtemp(prefix=prefix)) / name
    shutil.copytree(baseline, target)

    zero, zero_orig = target / "0", target / "0.orig"
    if zero_orig.is_dir():
        if zero.exists():
            shutil.rmtree(zero)
        shutil.copytree(zero_orig, zero)

    return target
