"""Shared fixtures for postProcessing tests."""

import pathlib
import subprocess

import pytest


def _run_or_dump_logs(script: str) -> None:
    """Run an Allrun-style script; on failure, dump the OpenFOAM log files so
    CI shows why the solver aborted instead of just 'exit status 134'."""
    result = subprocess.run([script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n===== {script} stdout =====\n{result.stdout}")
        print(f"\n===== {script} stderr =====\n{result.stderr}")
        for log in sorted(pathlib.Path.cwd().glob("log.*")):
            print(f"\n===== {log.name} (tail) =====")
            try:
                tail = log.read_text(errors="replace").splitlines()[-80:]
                print("\n".join(tail))
            except OSError as exc:
                print(f"(could not read {log.name}: {exc})")
        raise subprocess.CalledProcessError(
            result.returncode, [script], output=result.stdout, stderr=result.stderr
        )


@pytest.fixture(scope="function")
def run_reset_case(change_test_dir):
    """Reset OpenFOAM case before each test."""

    subprocess.run(["./Allclean"], check=True)
    _run_or_dump_logs("./Allrun")
    yield
    subprocess.run(["./Allclean"], check=True)


@pytest.fixture(scope="function")
def run_reset_case_parallel(change_test_dir):
    """Run OpenFOAM case in parallel, then clean up."""

    subprocess.run(["./Allclean"], check=True)
    _run_or_dump_logs("./AllrunParallel")
    yield
    subprocess.run(["./Allclean"], check=True)


# Re-export the fixture so it's available to tests in this directory
__all__ = ["run_reset_case", "run_reset_case_parallel"]
