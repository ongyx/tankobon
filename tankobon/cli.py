# coding: utf8

import collections
import functools
import json
import logging
import pathlib

import click
import coloredlogs  # type: ignore

try:
    import fpdf
    import imagesize
    from natsort import natsorted
except ImportError:
    fpdf = None
    imagesize = None
    natsort = None

from . import __version__, core, parsers  # noqa: F401
from .exceptions import MangaNotFoundError

click.option = functools.partial(click.option, show_default=True)  # type: ignore

_log = logging.getLogger("tankobon")
VERBOSITY = [
    getattr(logging, level)
    for level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
]

MANIFEST_PATH = "manifest.json"
A4_WIDTH = 210
A4_HEIGHT = 297


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

    for _, chapter in manga.data.items():
        volumes[chapter.volume].append(chapter)

    click.echo("| volume | chapter | title ")
    click.echo("|--------|---------|-------")

    for volume, chapters in volumes.items():
        for chapter in chapters:
            click.echo(
                "| {:<6} | {:<7} | {}".format(
                    volume, chapter.id, chapter.title or "(empty)"
                )
            )

    n_vol = len(volumes)
    n_chapter = len(manga.data)

    click.echo(
        f"summary: {n_vol} volume{'s' if n_vol > 1 else ''}, {n_chapter} chapter{'s' if n_chapter > 1 else ''}"
    )


def _load(url, cache):
    try:
        return cache.load(url)
    except MangaNotFoundError:
        click.echo(
            f"Manga not found in the cache. Try adding it first with 'tankobon refresh {url}'."
        )
        raise click.Abort()


@cli.command()
@click.argument("url")
@click.option("-c", "--chapter", help="show info only for a specific chapter")
def info(url, chapter):
    """Show info on a manga url."""

    with core.Cache() as cache:

        manga = _load(url, cache)

        if url not in cache.index:
            cache.save(manga)

        if chapter:
            _pprint(manga.data[chapter].__dict__)
        else:
            _info(manga)


@cli.command("list")
def _list():
    """List all manga in the cache."""

    _pprint({"supported websites": list(core.Manga.registered.keys())})

    click.echo("cached manga:\n")

    with core.Cache() as cache:

        if not cache.index:
            click.echo("(none)")

        else:
            for url, metadata in cache.index.items():
                print(f"{url}: {metadata['title']} ({metadata['_hash']})")


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

        if url not in cache.index:
            click.echo("manga dosen't exist, creating")
            manga = core.Manga.from_url(url)

        else:
            click.echo("loading existing manga")
            manga = cache.load(url)

        manga.refresh(pages=pages)

        click.echo("saving changes")
        cache.save(manga)


@cli.command()
@click.argument("url")
def delete(url):
    """Delete a manga by url from the cache."""

    with core.Cache() as cache:
        cache.delete(url)


@cli.command()
@click.argument("url")
@click.option(
    "-p",
    "--path",
    type=pathlib.Path,
    default=".",
    help="where to download to (must be a folder)",
)
@click.option(
    "-c", "--chapters", help="chapters to download, seperated by ',' (i.e '1,2,3,4')"
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="re-download chapters even if they have already been downloaded",
)
def download(url, path, chapters, force):
    """Download a manga by url."""

    try:
        with (path / MANIFEST_PATH).open() as f:
            manifest = json.load(f)
    except FileNotFoundError:
        manifest = {}

    with core.Cache() as cache:

        manga = _load(url, cache)

        if chapters is None:
            if click.confirm(
                "ALL chapters will be downloaded (this consumes a lot of bandwidth). Are you sure?"
            ):
                chapters = list(manga.data)
        else:
            chapters = chapters.split(",")

        for cid in chapters:
            click.echo(f"downloading chapter {cid}")

            if cid in manifest and not force:
                click.echo(f"chapter {cid} already downloaded, skipping")
                continue

            chapter_path = path / cid
            chapter_path.mkdir(exist_ok=True)

            try:
                images = manga.download(cid, chapter_path)
            except core.PagesNotFoundError:
                click.echo(
                    f"Pages for chapter {cid} not found. Try running 'tankobon refresh -p {url}' first."
                )
                raise click.Abort()

            manifest[cid] = natsorted(
                [str(i.relative_to(chapter_path)) for i in images]
            )

    with (path / MANIFEST_PATH).open("w") as f:
        json.dump(manifest, f, indent=4)


@cli.command()
@click.option(
    "-p",
    "--path",
    default=".",
    type=pathlib.Path,
    help="manga folder to make a pdf for",
)
@click.option(
    "-c", "--chapters", help="only add specific chapters to the pdf, split by ','"
)
@click.option(
    "-o",
    "--output",
    type=pathlib.Path,
    default="export.pdf",
    help="where to save the pdf",
)
def pdfify(path, chapters, output):
    """Create a (single) pdf file for several or more chapters of a downloade manga."""

    try:
        with (path / MANIFEST_PATH).open() as f:
            manifest = json.load(f)
    except FileNotFoundError:
        click.echo(
            "Can't seem to find the manifest file. Did you download the manga to another folder?"
        )
        raise click.Abort()

    if chapters is None:
        chapters = list(manifest.keys())
    else:
        chapters = chapters.split(",")

    document = fpdf.FPDF()

    for cid in natsorted(chapters):
        click.echo(f"adding chapter {cid}")

        chapter = manifest[cid]
        total = len(chapter) - 1
        for page in natsorted(chapter):
            click.echo(f"adding page {page} of {total}")
            page_path = path / cid / page

            width, height = imagesize.get(page_path)
            ratio = min(A4_WIDTH / width, A4_HEIGHT / height)

            document.add_page()
            document.image(str(page_path), 0, 0, w=width * ratio, h=height * ratio)

    document.output(str(path / output), "F")
