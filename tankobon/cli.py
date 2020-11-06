# coding: utf8

import json
import logging
import pathlib
import zipfile
from functools import partial

import click

from tankobon.__version__ import __version__
from tankobon.base import Cache
from tankobon.bootstraps import Bootstrap, update_index
from tankobon.utils import THREADS

# monkey-patch options
click.option = partial(click.option, show_default=True)  # type: ignore
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
def list():
    """List all mangas available."""
    for manga in Bootstrap.available:
        name = Bootstrap(manga).manga.DEFAULTS["title"]
        click.echo(f"{manga} ({name})")


@cli.command()
@click.argument("name")
def info(name):
    """Get info on a manga bootstrap."""
    manga = Bootstrap(name)()
    click.echo(f"Title: {manga.title}")
    click.echo(f"URL: {manga.url}")
    click.echo(f"Chapters:")
    for chapter in sorted(manga.chapters, key=float):
        chapter_info = manga.chapters[chapter]
        click.echo(f"{chapter}: {chapter_info['title']} ({chapter_info['url']})")


@cli.command()
@click.argument("name")
@click.option("-p", "--path", help="where to download to", default=".")
@click.option(
    "-t",
    "--threads",
    help="how many threads to use to download the manga",
    default=THREADS,
)
@click.option(
    "-r", "--refresh", help="whether or not to parse any new chapters", is_flag=True
)
@click.option(
    "-c",
    "--chapters",
    help="which chapters to download, seperated by slashes",
    default="all",
)
def download(name, path, threads, refresh, chapters):
    """Download a manga with name."""
    manga = Bootstrap(name)()

    if refresh:
        manga.refresh()

    with Cache(path, database=manga.database) as c:
        if chapters == "all":
            chapters = None
        else:
            chapters = chapters.split("/")

        c.download_chapters(ids=chapters, threads=threads)


@cli.command()
def update():
    """Update all manga bootstraps (in the index)."""
    update_index()


if __name__ == "__main__":
    cli()
