# coding: utf8

import logging
import pathlib
from functools import partial
from urllib.parse import urlparse

import click
import coloredlogs
import natsort

from tankobon.__version__ import __version__
from tankobon.store import STORES, Store
from tankobon.utils import THREADS, get_soup

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
    coloredlogs.install(
        level=VERBOSITY[verbosity - 1],
        fmt=" %(levelname)-8s :: %(message)s",
        logger=_log,
    )


@cli.group()
def store():
    """Manage stores."""


@store.command()
def list():
    """List all stores available, and their downloaded mangas."""
    for k, v in Store._index.items():
        click.echo(f"{k}/")
        spacing = " " * len(k)
        for m, t in v.items():
            click.echo(f"{spacing}{m} ({t['title']})")


def _print_chapter_info(database):
    for key in ("title", "url"):
        click.echo(f"{key.title()}: {database[key]}")
    click.echo(f"# of pages: {len(database['pages'])}")


@store.command()
@click.argument("name")
@click.option("-c", "--chapter", help="get info on a specific chapter", default="none")
def info(name, chapter):
    """Show infomation on a specific manga, where name is in the format 'store_name/manga_name'."""
    store_name, _, manga_name = name.partition("/")
    database = Store._index[store_name][manga_name]

    if chapter != "none":
        _print_chapter_info(database["chapters"][chapter])

    else:
        for k in natsort.natsorted(database["chapters"]):
            _print_chapter_info(database["chapters"][k])
            click.echo("")


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
    "-v",
    "--volumes",
    help="which volumes to create a pdf for, seperated by slashes",
    default="all",
)
@click.option(
    "-n",
    "--no-download",
    help="only parse all pages without downloading them",
    is_flag=True,
    default=False,
)
# @click.option(
#    "-f",
#    "--force",
#    help="reparse all chapters and pages, regardless whether or not they have already been parsed",
#    is_flag=True,
#    default=False,
# )
def download(url, path, threads, refresh, volumes, no_download):
    """Download a manga from url to path."""
    # the url acts as the id here
    path = pathlib.Path(path)
    path.mkdir(exist_ok=True)

    volumes = None if volumes == "all" else volumes.split("/")

    store = Store(url, update=True)
    with store as manga:

        if no_download:
            manga.parse()
        else:
            manga.download_volumes(path, volumes)

        _ = manga.database.pop("url")  # we use the url as the manga id anyway..
        store.database = manga.database


if __name__ == "__main__":
    cli()
