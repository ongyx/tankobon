# coding: utf8

import functools
import logging
import pathlib
from typing import Any, Callable

import click
import coloredlogs  # type: ignore

from .. import __version__, core, iso639, utils
from ..sources.base import Parser

from ..exceptions import MangaNotFoundError

from . import common

click.option: Callable[..., Any] = functools.partial(click.option, show_default=True)  # type: ignore

_log = logging.getLogger("tankobon")

CONFIG = utils.CONFIG
CONFIG_TYPES = [int, float, str]


def prettyprint(dict_, indent=0):

    for key, value in dict_.items():

        # +2 for the ': ' suffix
        indent_ = indent + len(key) + 2

        if isinstance(value, list):
            value = f"\n{' ' * indent_}".join(value)

        elif isinstance(value, dict):
            if CONFIG["lang"] in value or "en" in value:
                # a localised field of some kind.
                value = value.get(CONFIG["lang"]) or value["en"]

        click.echo(f"{key}: {value}\n")


def _load(shorthash, cache):
    try:
        return cache.load(cache.fullhash(shorthash))
    except MangaNotFoundError:
        click.echo(
            f"Manga not found in the cache. Try adding it first with 'tankobon add {shorthash}'."
        )
        raise click.Abort()


@click.group()
@click.version_option(__version__)
def cli():
    """Manga browser/downloader.

    Once a manga has been added to tankobon using 'tankobon add <url>',
    you can refer to it using its shorthash (first 8 characters of its SHA512 hash).

    Executing 'tankobon list' will show the shorthashes of all manga added to tankobon.
    """
    # set up logger
    coloredlogs.install(
        level=getattr(logging, CONFIG["log.level"]),
        fmt=" %(levelname)-8s :: %(message)s",
        logger=_log,
    )


def to_native(s):
    if s in ("true", "false"):
        return s == "true"

    for _type in CONFIG_TYPES:
        try:
            return _type(s)
        except ValueError:
            pass

    return None


@cli.command()
@click.argument("pair", nargs=-1)
def config(pair):
    """Configure tankobon.

    \b
    This command can be used several ways:

    \b
    'tankobon config' - list all keys and values
    'tankobon config (key)' - show value for key
    'tankobon config (key) (value)' - set key to value
    """

    pair = list(pair[:2])
    while len(pair) < 2:
        pair.append(None)

    key, value = pair

    if key is None:
        for key, value in CONFIG.items():
            click.echo(f"{key}: {value}")
    else:
        if value is None:
            click.echo(CONFIG[key])
        else:
            CONFIG[key] = to_native(value)


@cli.command()
@click.argument("shorthash")
@click.option("-c", "--chapter", help="show info only for a specific chapter")
def info(shorthash, chapter):
    """Show info on a manga."""

    with core.Cache() as cache:

        manga = _load(shorthash, cache)
        info = manga.info

        if chapter:
            prettyprint(manga.chapters[chapter][CONFIG["lang"]].__dict__)
        else:
            prettyprint(manga.meta.__dict__)

            prettyprint({"languages": common.describe_langs(info["langs"])})

            click.echo(manga.summary(lang=CONFIG["lang"], link=False))

            click.echo(
                "summary: "
                f"{utils.plural(len(info['volumes']), 'volume')}, "
                f"{utils.plural(info['chapters'], 'chapter')}"
            )


@cli.command("list")
def _list():
    """List all manga in the cache."""

    prettyprint(
        {"supported websites": [cls.domain.pattern for cls in Parser.registered]}
    )

    with core.Cache() as cache:

        if not cache.data:
            click.echo("(none)")

        else:
            for hash, manga in cache.data.items():
                meta = manga["meta"]

                print(f"{hash[:core.SHORT_HASH_LEN]}: {meta.title} ({meta.url})")


def _refresh(manga):
    parser = Parser.by_url(manga.meta.url)
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

        parser = Parser.by_url(url)
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
    downloader = core.Downloader(path)

    manga = _load(shorthash, cache)
    parser = Parser.by_url(manga.meta.url)

    if cids is None:
        if not click.confirm(
            "ALL chapters will be downloaded (this consumes a lot of bandwidth). Are you sure?"
        ):
            raise click.Abort()

        chapters = []

        for _, langs in manga.chapters.items():
            chapter = langs.get(CONFIG["lang"])
            if chapter is not None:
                chapters.append(chapter)

    else:
        chapters = manga.select(cids, lang=CONFIG["lang"])

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

        downloader.pdfify(chapters, output, lang=CONFIG["lang"])


@cli.command("gui")
def _gui():
    """Start the tankobon GUI."""

    try:
        from . import gui

    except ImportError:
        click.echo(
            "GUI extension not installed, install with 'pip install tankobon[gui]'."
        )
        raise click.Abort()

    else:
        gui.main()


def main():
    try:
        cli()
    finally:
        CONFIG.close()
