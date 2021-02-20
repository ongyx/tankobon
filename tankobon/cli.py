# coding: utf8

import collections
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


def _parse(url, **kwargs):
    with parsers.Cache() as cache, cache.load(url) as parser:
        parser.parse(**kwargs)
        cache.dump(parser)
        return parser.data


def _info(metadata):
    for key in ("title", "url", "description"):
        click.echo(f"{key}: {metadata[key]}\n")

    volumes = collections.defaultdict(list)
    for chapter, data in metadata["chapters"].items():
        volumes[data["volume"]].append(chapter)

    click.echo()

    click.echo("| volumes | chapters")
    for volume, chapters in volumes.items():

        chapters_str = f",\n| {' ' * 7} | ".join(
            ", ".join(chapters[c : c + MAX_COLUMNS])
            for c in range(0, len(chapters), MAX_COLUMNS)
        )
        click.echo("| {:<7} | {}".format(volume, chapters_str))

    click.echo(
        f"summary: {len(volumes)} volume(s), {len(metadata['chapters'])} chapter(s)"
    )


@cli.command()
@click.option("-u", "--url", default="", help="show info on a specific manga")
def info(url):
    """Show info on parsed/downloaded manga."""
    with parsers.Cache() as cache:
        if url:
            data = cache.load_metadata(url)
            if data.get("title") is None:
                click.echo(f"manga not found, run 'tankobon parse {url}' first")
                return

            _info(data)
        else:
            for url, name in cache._index.items():
                click.echo(f"{url}: {name}")


@cli.command()
@click.argument("url")
@click.option(
    "-f", "--force", default=False, is_flag=True, help="ignore existing metadata"
)
def parse(url, force):
    """Parse a manga's metadata from url and cache it on disk."""
    _parse(url, force=force)


@cli.command()
@click.argument("url")
@click.option("-p", "--path", default=".", help="where to download to")
@click.option(
    "-c",
    "--chapters",
    default="all",
    help="chapters to download, seperated by slashes (ignored if export-pdf is specified)",
)
@click.option(
    "-f", "--force", default=False, is_flag=True, help="re-download existing pages"
)
@click.option(
    "-e",
    "--export-pdf",
    default="",
    help="volumes to create pdfs for, seperated by slashes",
)
def download(url, path, chapters, force, export_pdf):
    """Download a manga's pages by name/url."""
    data = _parse(url, force=False, volume=export_pdf or None)

    if chapters == "all":
        chapters_list = list(data["chapters"])
    else:
        chapters_list = chapters.split("/")

    downloader = manga.Downloader(data)

    if export_pdf != "none":
        # download only the chapters in the volume(s)
        for volume in export_pdf.split("/"):
            downloader.export_pdf(volume, path)
    else:
        downloader.download(path, chapters=chapters_list, force=force)


if __name__ == "__main__":
    cli(prog_name="tankobon")
