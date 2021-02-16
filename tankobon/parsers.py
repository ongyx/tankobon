# coding: utf8
"""This directory contains parsers for several websites.

Parsers are analogous to youtube-dl extractors: they define how to parse out infomation of a manga on a webpage.
Parsers *must* subclass and satisfy the tankobon.manga.Parser interface.

Typically, parsers make heavy use of regexes and leverage the BeautifulSoup API through the .soup attribute:

>>> class MyParser(Parser):
...
...     # The domain of the website you are going to parse, *without* a 'www' in front.
...     domain = "my-website.com"
...
...     def chapters(self):
...         for tag in self.soup.find_all("div"):
...             yield {
...                 "id": tag.h1.text,
...                 "title": tag.h2.text,
...                 "url": tag.a["href"]
...             }
...
...     def pages(self, soup):
...         return [tag["href"] for tag in soup.find_all("a", href=True)]

When subclassed, the new parser will automatically be registered.
The parser will then be delegated to based on the domain name (using urlparse's netloc):

>>> from tankobon import parsers
>>> parser = parsers.load({"url": "https://my-website.com/manga/12345"})
"""

import json
import pathlib

from tankobon import manga, utils

# import for side effects (register parsers)
from tankobon._parsers import (  # noqa: W0611 type: ignore
    mangadex,
    mangabat,
    mangakakalot,
    komi_san,
)

# Manga metadata is stored here using a filename-safe version of its title.
CACHE_PATH = pathlib.Path.home() / ".tankobon"
CACHE_PATH.mkdir(exist_ok=True)


def _create_filename(parser):
    return f"{utils.sanitize_filename(parser.title())}.json"


def load(*args, **kwargs) -> manga.Parser:
    """Load a parser and initalize it with the given arguments.
    The parser to be loaded will be based on the domain of data['url'] (the data argument).


    Args:
        *args: Passed to the parser.
        **kwargs: Passed to the parser.

    Raises:
        ValueError, if the data arg is not passed or the parser for the website's domain does not exist.

    Returns:
        The parser.
    """

    try:
        data = kwargs.get("data") or args[0]
    except IndexError:
        raise ValueError("no data arg (can't determine parser to use without url)")

    domain = utils.parse_domain(data["url"])

    parser = manga._parsers.get(domain)
    if parser is None:
        raise ValueError(f"no parser exists for domain {domain}")

    return parser(*args, **kwargs)


class Cache:
    """A cache for manga metadata."""

    def __init__(self, path: pathlib.Path = CACHE_PATH):
        self._path = path

    @property
    def manga_names(self):
        return [p.stem for p in self._path.glob("*.json")]

    def load(self, url: str) -> manga.Parser:
        """Initalize a parser by url with its previously cached metadata.

        Args:
            url: The manga website url.

        Returns:
            The parser.
        """

        parser = load({"url": url})

        metadata = self._path / _create_filename(parser)

        if metadata.is_file():
            with metadata.open() as f:
                parser.data.update(json.load(f))

        return parser

    def loads(self, name: str) -> manga.Parser:
        """Initalize a parser by name with its previous cached metadata.

        name: The manga name.
            Loadable manga names can be accessed through .manga_names.

        Returns:
            The parser.
        """

        metadata = self._path / name

        with metadata.open() as f:
            return load(json.load(f))

    def dump(self, parser: manga.Parser) -> None:
        """Cache the updated metadata of a parser.

        Args:
            parser: The manga parser.
        """

        metadata = self._path / _create_filename(parser)

        with metadata.open("w") as f:
            json.dump(parser.data, f, indent=4)
