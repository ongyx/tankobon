# coding: utf8

import logging
import os
import pathlib
from functools import partial

import click
import coloredlogs
import natsort

from tankobon.__version__ import __version__
from tankobon.store import Store

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
def show():
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
@click.option("-d", "--dir", help="where to download to", default=".")
@click.option(
    "-p",
    "--pdf",
    help=(
        "which volumes to create a pdf for, seperated by slashes (1/2/3). "
        "Note that any chapters in the volume not explicitly specified with --chapters will be downloaded."
    ),
    default="none",
)
@click.option(
    "-n",
    "--no-download",
    help="only parse all pages without downloading any",
    is_flag=True,
    default=False,
)
@click.option(
    "-i",
    "--index",
    help="path to the index.json file (can also be set using 'TANKOBON_INDEX' env variable",
    default="",
)
@click.option(
    "-c",
    "--chapters",
    help="chapters to download, seperated by slashes (1/2/3) or a range (1-3). Both can be mixed: (1/2-5).",
    default="all",
)
def download(url, dir, pdf, no_download, index, chapters):
    """Download a manga from url to path."""
    # the url acts as the id here
    dir = pathlib.Path(dir)
    dir.mkdir(exist_ok=True)

    if not index:
        index = os.environ.get("TANKOBON_INDEX")

    if url.endswith("/"):
        url = url[:-1]

    store = Store(url, index_path=index, update=True)
    with store as manga:

        all_chapters = manga.sorted()
        if chapters == "all":
            chapters_to_download = set(all_chapters)
        else:
            chapters_to_download = set()
            for chapter in chapters.split("/"):
                if "-" in chapter:
                    start, end = chapter.split("-")
                    for c in all_chapters[
                        all_chapters.index(start) : all_chapters.index(end) + 1
                    ]:
                        chapters_to_download.add(c)
                else:
                    chapters_to_download.add(chapter)

        try:
            if no_download:
                manga.parse()
            else:
                if chapters != "all":
                    # download user requested chapters
                    manga.download_chapters(dir, chapters=list(chapters_to_download))

                elif pdf != "none":
                    # download user requested volumes
                    manga.download_volumes(dir, volumes=pdf.split("/"))

                else:
                    # download all chapters
                    manga.download_chapters(dir)

            _ = manga.database.pop("url")  # we use the url as the manga id anyway..
        finally:
            _log.info("[database] syncing to disk")
            store.database = manga.database


if __name__ == "__main__":
    cli()
