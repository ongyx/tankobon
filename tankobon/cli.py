# coding: utf8

import collections
import functools
import logging
import pathlib

import click
import coloredlogs  # type: ignore

from . import __version__, core, parsers

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


def _info(manga):
    metadata = manga.meta.__dict__

    for key in ("title", "url", "description"):
        click.echo(f"{key}: {metadata[key]}\n")

    volumes = collections.defaultdict(list)

    for _, chapter in manga.chapter_data.items():
        volumes[chapter.volume].append(chapter.id)

    click.echo("\n| volumes | chapters")
    for volume, chapters in volumes.items():

        chapters_str = f",\n| {' ' * 7} | ".join(
            ", ".join(chapters[c : c + MAX_COLUMNS])
            for c in range(0, len(chapters), MAX_COLUMNS)
        )
        click.echo("| {:<7} | {}".format(volume, chapters_str))

    click.echo(f"summary: {len(volumes)} volume(s), {len(metadata)} chapter(s)")
