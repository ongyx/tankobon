# coding: utf8

import functools
import logging

import click
import coloredlogs  # type: ignore

from tankobon import __version__, manga, parsers

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


def _parse(url, force):
    with cache.load(url) as parser:
        parser.parse(force=force)
        cache.dump(parser)
        return parser.data


@cli.command()
@click.argument("url")
@click.option(
    "-f", "--force", default=False, is_flag=True, help="ignore existing metadata"
)
def parse(url, force):
    """Parse a manga's metadata from url and cache it on disk."""
    _parse(url, force)


@cli.command()
@click.argument("url")
@click.option("-p", "--path", default=".", help="where to download to")
@click.option(
    "-c",
    "--chapters",
    default="all",
    help="chapters to download, seperated by slashes ('/')",
)
@click.option(
    "-f", "--force", default=False, is_flag=True, help="re-download existing pages"
)
def download(url, path, chapters, force):
    """Download a manga's pages."""
    data = _parse(url, False)

    if chapters == "all":
        chapters = list(data["chapters"])
    else:
        chapters = chapters.split("/")

    downloader = manga.Downloader(data)
    downloader.download(path, chapters=chapters, force=force)


if __name__ == "__main__":
    cli(prog_name="tankobon")
