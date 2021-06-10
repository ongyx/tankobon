# coding: utf8

import functools
import logging
import pathlib
from typing import Any, Callable

import click
import coloredlogs  # type: ignore

from . import __version__, core, sources, utils  # noqa: F401
from .exceptions import MangaNotFoundError

click.option: Callable[..., Any] = functools.partial(click.option, show_default=True)  # type: ignore

_log = logging.getLogger("tankobon")
VERBOSITY = [
    getattr(logging, level)
    for level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
]

CONFIG = utils.Config()
LANG = CONFIG["lang"]


@click.group()
@click.version_option(__version__)
@click.option(
    "-v", "--verbose", "verbosity", help="be more chatty", default=4, count=True
)
def cli(verbosity):
    """Manga browser/downloader.

    Once a manga has been added to tankobon using 'tankobon add <url>',
    you can refer to it using its shorthash (first 8 characters of its SHA512 hash).

    Executing 'tankobon list' will show the shorthashes of all manga added to tankobon.
    """
    # set up logger
    coloredlogs.install(
        level=VERBOSITY[verbosity - 1],
        fmt=" %(levelname)-8s :: %(message)s",
        logger=_log,
    )


def prettyprint(dict_):

    for key, value in dict_.items():

        # +2 for the ': ' suffix
        indent = len(key) + 2

        if isinstance(value, list):
            value = f"\n{' ' * indent}".join(value)

        click.echo(f"{key}: {value}\n")


def _load(shorthash, cache):
    try:
        return cache.load(cache.fullhash(shorthash))
    except MangaNotFoundError:
        click.echo(
            f"Manga not found in the cache. Try adding it first with 'tankobon add {shorthash}'."
        )
        raise click.Abort()


@cli.command()
@click.argument("shorthash")
@click.option("-c", "--chapter", help="show info only for a specific chapter")
def info(shorthash, chapter):
    """Show info on a manga."""

    with core.Cache() as cache:

        manga = _load(shorthash, cache)

        if chapter:
            prettyprint(manga.chapters[chapter].__dict__)
        else:
            prettyprint(manga.meta.__dict__)

            click.echo(manga.summary())

            info = manga.info

            click.echo(
                "summary: "
                f"{utils.plural(len(info['volumes']), 'volume')}, "
                f"{utils.plural(info['chapters'], 'chapter')}\n"
                f"languages: {', '.join(info['langs'])}"
            )


@cli.command("list")
def _list():
    """List all manga in the cache."""

    prettyprint(
        {"supported websites": [cls.domain.pattern for cls in core.Parser.registered]}
    )

    with core.Cache() as cache:

        if not cache.data:
            click.echo("(none)")

        else:
            for hash, manga in cache.data.items():
                meta = manga["meta"]

                print(f"{hash[:core.SHORT_HASH_LEN]}: {meta.title} ({meta.url})")


def _refresh(manga):
    parser = core.Parser.parser(manga.meta.url)
    parser.add_chapters(manga)


@cli.command()
@click.argument("url")
def add(url):
    """Create a manga by url."""

    with core.Cache() as cache:

        if url in cache.alias:
            short_hash = cache.alias[url][: core.SHORT_HASH_LEN]

            click.echo(
                f"manga already exists (refresh with 'tankobon refresh {short_hash}')"
            )
            return

        parser = core.Parser.parser(url)
        manga = parser.create(url)

        _refresh(manga)

        cache.dump(manga)

        click.echo(
            f"Sucessfully added '{url}'! It's shorthash is <{manga.meta.hash[:core.SHORT_HASH_LEN]}>."
        )


@cli.command()
@click.argument("shorthash")
def refresh(shorthash):
    """Refresh a manga by shorthash (adds any new chapters)."""

    with core.Cache() as cache:

        manga = _load(shorthash, cache)
        _refresh(manga)
        cache.dump(manga)


@cli.command()
@click.argument("shorthash")
def remove(shorthash):
    """Delete a manga by shorthash from the cache."""

    with core.Cache() as cache:
        cache.delete(cache.fullhash(shorthash))


@cli.command()
@click.argument("shorthash")
@click.option(
    "-p",
    "--path",
    type=pathlib.Path,
    default=".",
    help="where to download to (must be a folder)",
)
@click.option(
    "-c",
    "--chapters",
    "cids",
    help=(
        "chapters to download, seperated by ','. "
        "Ranges are also allowed (i.e '1-5,10' - download chapters 1 to 5 and 10)."
    ),
)
@click.option("-f", "--force", help="redownload existing chapters", default=False)
def download(shorthash, path, cids, force):
    """Download a manga by shorthash."""

    cache = core.Cache()
    parser = core.Parser.parser(shorthash)
    downloader = core.Downloader(path)

    manga = _load(shorthash, cache)

    if cids is None:
        if not click.confirm(
            "ALL chapters will be downloaded (this consumes a lot of bandwidth). Are you sure?"
        ):
            raise click.Abort()

        chapters = []

        for _, langs in manga.chapters.items():
            chapter = langs.get(LANG)
            if chapter is not None:
                chapters.append(chapter)

    else:
        chapters = manga.select(cids, lang=LANG)

    for chapter in chapters:
        click.echo(f"downloading chapter {chapter.id}")

        if not chapter.pages:
            click.echo(f"chapter {chapter.id} does not have any pages, adding")
            parser.add_pages(chapter)

        downloader.download(chapter, force=force)

    cache.close()
    downloader.close()


@cli.command()
@click.option(
    "-p",
    "--path",
    default=".",
    help="manga folder to make a pdf for",
)
@click.option(
    "-c", "--chapters", help="only add specific chapters to the pdf, split by ','"
)
@click.option(
    "-o",
    "--output",
    default="export.pdf",
    help="where to save the pdf",
)
def pdfify(path, chapters, output):
    """Create a (single) pdf file for all chapters of a downloaded manga."""

    with core.Downloader(path) as downloader:
        if chapters is None:
            chapters = list(downloader.manifest.keys())
        else:
            chapters = chapters.split(",")

        downloader.pdfify(chapters, output, lang=LANG)


@cli.command("gui")
def _gui():
    """Start the tankobon GUI."""

    try:
        from .gui import gui

    except ImportError:
        click.echo(
            "GUI extension not installed, install with 'pip install tankobon[gui]'."
        )
        raise click.Abort()

    else:
        gui.main()
