# coding: utf8

import functools
import logging

import click
import coloredlogs  # type: ignore

from tankobon import __version__, parsers

click.option = functools.partial(click.option, show_default=True)  # type: ignore

_log = logging.getLogger("tankobon")
VERBOSITY = [
    getattr(logging, level)
    for level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
]

cache = parsers.Cache()


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


@cli.command()
@click.argument("url")
@click.option(
    "-f", "--force", default=False, is_flag=True, help="ignore existing metadata"
)
def parse(url, force):
    """Parse a manga's metadata from url and cache it on disk."""

    with cache.load(url) as parser:
        parser.parse(force=force)
        cache.dump(parser)


if __name__ == "__main__":
    cli(prog_name="tankobon")
