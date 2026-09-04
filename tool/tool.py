from pathlib import Path

import click


@click.group()
def cli() -> None:
    """Tools for checking localisation release files."""


@cli.command()
@click.argument("plist_old", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("plist_new", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def verify(plist_old: Path, plist_new: Path) -> None:
    """Print localisation changes and risks to the terminal."""
    click.echo(f"Comparing {plist_old} -> {plist_new}")
