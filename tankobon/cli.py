# coding: utf8

import collections
import functools
import logging
import pathlib

import click
import coloredlogs  # type: ignore

from . import __version__, core, parsers  # noqa: F401

click.option = functools.partial(click.option, show_default=True)  # type: ignore

_log = logging.getLogger("tankobon")
VERBOSITY = [
    getattr(logging, level)
    for level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
]

MAX_COLUMNS = 10


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


def _pprint(_dict):

    for key, value in _dict.items():

        # +2 for the ': ' suffix
        indent = len(key) + 2

        if isinstance(value, list):
            value = f"\n{' ' * indent}".join(value)

        click.echo(f"{key}: {value}\n")


def _info(manga):

    _pprint(manga.meta.__dict__)

    volumes = collections.defaultdict(list)

    for _, chapter in manga.chapter_data.items():
        volumes[chapter.volume].append(chapter.id)

    click.echo("| volumes | chapters")
    for volume, chapters in volumes.items():

        chapters_str = f",\n| {' ' * 7} | ".join(
            ", ".join(chapters[c : c + MAX_COLUMNS])
            for c in range(0, len(chapters), MAX_COLUMNS)
        )
        click.echo("| {:<7} | {}".format(volume, chapters_str))

    n_vol = len(volumes)
    n_chapter = len(manga.chapter_data)

    click.echo(
        f"summary: {n_vol} volume{'s' if n_vol > 1 else ''}, {n_chapter} chapter{'s' if n_chapter > 1 else ''}"
    )


@cli.command()
@click.argument("url")
@click.option("-c", "--chapter", help="show info only for a specific chapter")
def info(url, chapter):
    """Show info on a manga url."""

    with core.Cache() as cache:

        manga = cache.load(url)

        if url not in cache.index:
            cache.save(manga)

        if chapter:
            _pprint(manga.chapter_data[chapter].__dict__)
        else:
            _info(manga)


@cli.command()
@click.argument("url")
@click.option(
    "-p",
    "--pages",
    is_flag=True,
    help="parse pages for chapters without any pages",
)
def refresh(url, pages):
    """Create/refresh data for a manga by url.
    You can add manga urls using this command (it will be created if it does not exist).
    """

    with core.Cache() as cache:

        manga = cache.load(url)

        manga.refresh(pages=pages)

        cache.save(manga)


@cli.command()
@click.argument("url")
def delete(url):
    """Delete a manga by url from the cache."""

    with core.Cache() as cache:
        cache.delete(url)
