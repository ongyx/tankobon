# coding: utf8

import logging
import pathlib
from functools import partial
from urllib.parse import urlparse

import click
import coloredlogs

from tankobon.__version__ import __version__
from tankobon.store import STORES, Store
from tankobon.utils import THREADS, get_soup

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
    database = Store._index["stores"][store_name][manga_name]

    if chapter != "none":
        _print_chapter_info(database["chapters"][chapter])

    else:
        for k in sorted(database["chapters"], key=float):
            _print_chapter_info(database["chapters"][k])
            click.echo("")


@store.command()
@click.option(
    "-s", "--store_name", help="update only for a specific store/manga", default="all"
)
def update(store_name):
    """Update all previously downloaded mangas."""
    if "/" in store_name:
        store_name, _, manga_name = store_name.partition("/")
    else:
        manga_name = None

    if store_name == "all":
        _log.info("updating all mangas")
        for store, mangas in Store._index["stores"].items():
            for manga in mangas:
                with Store(store, manga) as m:
                    _log.info(f"updating {store}:{manga}")
                    m.parse_all()
    else:
        _log.info(f"updating mangas for store {store_name}")
        if manga_name:
            mangas = [manga_name]
        else:
            mangas = Store._index["stores"][store_name]

        for manga in mangas:
            with Store(store_name, manga) as m:
                _log.info(f"updating {store}:{manga}")
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
@click.option(
    "-p",
    "--parse",
    help="only parse all pages without downloading them",
    is_flag=True,
    default=False,
)
@click.option(
    "-f",
    "--force",
    help="reparse all chapters and pages, regardless whether or not they have already been parsed",
    is_flag=True,
    default=False,
)
def download(url, path, threads, refresh, chapters, parse, force):
    """Download a manga from url."""
    # the url acts as the id here
    store = Store(STORES[urlparse(url).netloc], url)
    if not store.database:
        store.database = {"url": url}

    manga = store.manga(store.database, force=force)

    if chapters != "all":
        chapters = chapters.split("/")
        for chapter in chapters:
            manga.parse_pages(get_soup(manga.database["chapters"][chapter]["url"]))
    else:
        chapters = None
        manga.parse_all()

    if not parse:
        manga.download_chapters(pathlib.Path(path), chapters)

    _ = manga.database.pop("url")
    store.database = manga.database
    store.close()


if __name__ == "__main__":
    cli()
