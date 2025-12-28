"""
Command-line interface for pyOFTools using Typer.
"""

from pathlib import Path

import typer

app = typer.Typer(
    name="pyoftools",
    help="Python tools for OpenFOAM operations",
    no_args_is_help=True,
)

# setfields_app = typer.Typer(
#     name="setfields",
#     help="SetFields functionality for OpenFOAM cases",
# )
# app.add_typer(setfields_app, name="setfields")


@app.command("setFields")
def setfields_dummy(
    case_dir: Path = typer.Option(".", "--case", "-C", help="OpenFOAM case directory"),
    field_name: str = typer.Option("alpha.water", "--field", "-f", help="Field name to set"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
) -> None:
    """Dummy setFields command - placeholder for future functionality."""

    typer.echo("SetFields dummy command called:")
    typer.echo(f"  Case directory: {case_dir}")
    typer.echo(f"  Field name: {field_name}")
    typer.echo(f"  Dry run: {dry_run}")

    if dry_run:
        typer.echo("This is a dry run - no files would be modified")
    else:
        typer.echo("This is a dummy function - no actual setFields operation performed")

    typer.echo("✓ Command completed successfully")


@app.command("version")
def version() -> None:
    """Show pyOFTools version."""
    from .. import __version__

    typer.echo(f"pyOFTools version: {__version__}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
