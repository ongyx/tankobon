# coding: utf8

import json
import logging
import pathlib
import zipfile

import click

from tankobon.base import Cache
from tankobon.bootstraps import Bootstrap
from tankobon.__version__ import __version__

VERBOSITY = (
    logging.CRITICAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
)
_log = logging.getLogger("tankobon")

CACHEPATH = pathlib.Path.home() / "Documents" / "tankobon"
BOOTSTRAP_PATH = pathlib.Path(__file__).parent / "bootstraps"


@click.group()
@click.version_option(__version__)
@click.option(
    "-v", "--verbose", "verbosity", help="be more chatty", default=4, count=True
)
def cli(verbosity):
    """Manga browser/downloader."""
    # set up logger
    _log.setLevel(VERBOSITY[verbosity - 1])


@cli.command()
@click.argument("name")
@click.option("-p", "--path", help="where to download to", default=".")
def download(name, path):
    f"""Download a manga with name (available: {", ".join(Bootstrap.available)})"""
    manga = Bootstrap(name)()
    with Cache(path, database=manga.database) as c:
        c.download_chapters()


if __name__ == "__main__":
    cli()
