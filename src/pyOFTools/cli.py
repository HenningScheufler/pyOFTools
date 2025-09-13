"""
Command-line interface for pyOFTools using Typer.
"""

import typer
from pathlib import Path
from typing import Optional
import runpy
import json

app = typer.Typer(
    name="pyoftools",
    help="Python tools for OpenFOAM operations",
    no_args_is_help=True,
)


@app.command("setFields")
def setfields(
    input_file: str,
    case_dir: Path = typer.Option(".", "--case", "-C", help="OpenFOAM case directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
):
    if input_file.endswith(".py"):
        typer.echo(f"Running Python setFields script: {input_file}")
        runpy.run_path(input_file, run_name="__main__")
    elif input_file.endswith(".json"):
        typer.echo(f"Loading setFields JSON: {input_file}")
        with open(input_file) as f:
            data = json.load(f)
        typer.echo(f"Loaded JSON: {data}")
    else:
        typer.echo("Error: Input file must be .py or .json", err=True)
        raise typer.Exit(1)

@app.command("version")
def version():
    """Show pyOFTools version."""
    from . import __version__

    typer.echo(f"pyOFTools version: {__version__}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
