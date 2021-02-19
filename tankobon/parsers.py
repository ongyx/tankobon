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

import collections
import importlib
import json
import pathlib

from tankobon import manga, utils

INDENT = 4

# Manga metadata is stored here using a filename-safe version of its title.
CACHE_PATH = pathlib.Path.home() / ".tankobon"
CACHE_PATH.mkdir(exist_ok=True)

# This file maps manga URLs to their filenames.
INDEX_PATH = CACHE_PATH / "_index.json"


def _register():
    # import for side effects (register default parser classes)
    for submodule in (pathlib.Path(__file__).parent / "_parsers").glob("*.py"):
        _ = importlib.import_module(f"tankobon._parsers.{submodule.stem}")


_register()


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
    if parser is not None:
        return parser(*args, **kwargs)

    # domain does not need to match _exactly_.
    # we don't need to mess around with TLDs, just do a substring check
    for parser_domain, parser in manga._parsers.items():
        if parser_domain in domain:
            return parser(*args, **kwargs)

    # no parser matches
    raise ValueError(f"no parser exists for domain {domain}")


class Index(collections.UserDict):
    """An index to keep track of manga metadata."""

    def __init__(self, path: pathlib.Path = INDEX_PATH):
        self._path = path
        try:
            with self._path.open() as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        super().__init__(data)

    def close(self):
        with self._path.open("w") as f:
            json.dump(self.data, f, indent=INDENT)


class Cache:
    """A cache for manga metadata."""

    def __init__(self, path: pathlib.Path = CACHE_PATH):
        self._path = path
        self._index = Index(self._path / "_index.json")

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    def close(self):
        self._index.close()

    @property
    def manga_names(self):
        return list(self._index.values())

    def load_metadata(self, url_or_name: str) -> dict:
        """Load metadata for a manga.

        Args:
            url_or_name: The manga url/name.
        """

        name = self._index.get(url_or_name) or url_or_name

        if name is not None:
            try:
                with (self._path / name).open() as f:
                    return json.load(f)
            except FileNotFoundError:
                pass

        # manga has no existing metadata
        return {"url": url_or_name}

    def load(self, url_or_name: str) -> manga.Parser:
        """Initalize a parser by url with its previously cached metadata.

        Args:
            url_or_name: The manga website url/filename-safe name (see .manga_names).

        Returns:
            The parser.
        """

        metadata = self.load_metadata(url_or_name)

        return load(data=metadata)

    def dump(self, parser: manga.Parser) -> None:
        """Cache the updated metadata of a parser.

        Args:
            parser: The manga parser.
        """

        name = _create_filename(parser)
        self._index[parser.data["url"]] = name

        with (self._path / name).open("w") as f:
            json.dump(parser.data, f, indent=INDENT)
