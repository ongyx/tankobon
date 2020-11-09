# coding: utf8

import json
import logging
import pathlib
from functools import partial
from urllib.parse import urlparse

import click
import coloredlogs

from tankobon.__version__ import __version__
from tankobon.store import Store, STORES, INDEX
from tankobon.utils import THREADS

coloredlogs.install(
    fmt=" %(levelname)-8s :: %(message)s",
    logger=logging.getLogger("tankobon"),
)

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


@click.group()
@click.version_option(__version__)
@click.option(
    "-v", "--verbose", "verbosity", help="be more chatty", default=4, count=True
)
def cli(verbosity):
    """Manga browser/downloader."""
    # set up logger
    _log.setLevel(VERBOSITY[verbosity - 1])


@cli.group()
def store():
    """Manage stores."""


@store.command()
def list():
    """List all stores available, and their downloaded mangas."""
    for k, v in Store._index["stores"].items():
        click.echo(f"{k}/")
        spacing = " " * len(k)
        for m, t in v.items():
            click.echo(f"{spacing}{m} ({t['title']})")


@store.command()
@click.option(
    "-s", "--store_name", help="update only for a specific store/manga", default="all"
)
def update(store_name):
    """Update all previously downloaded mangas."""
    if "/" in store_name:
        store_name, _, manga_name = store.partition("/")
    else:
        manga_name = None

    if store_name == "all":
        for store, mangas in Store._index["stores"].items():
            for manga in mangas:
                with Store(store, manga) as m:
                    m.parse_all()
    else:
        if manga_name:
            with Store(store_name, manga_name) as m:
                m.parse_all()
        else:
            for manga in Store._index["stores"][store_name]:
                with Store(store_name, manga_name) as m:
                    m.parse_all()


@cli.command()
@click.argument("url")
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
def download(url, path, threads, refresh, chapters):
    """Download a manga from url."""
    store = Store(STORES[urlparse(url).netloc], url)
    if store.database:
        manga = store.manga(store.database)
    else:
        manga = store.manga({"url": url})

    if chapters != "all":
        chapters = chapters.split("/")
        for chapter in chapters:
            manga.parse_pages(chapter)
    else:
        chapters = None
        manga.parse_all()

    manga.download_chapters(pathlib.Path(path), chapters)
    store.database = manga.database
    store.close()


if __name__ == "__main__":
    cli()
