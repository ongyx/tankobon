# coding: utf8
"""Utilities for tankobon."""

import collections
import gzip
import json
import logging
import os
import pathlib
import re
from typing import Optional, Union
from urllib.parse import urlparse

import bs4  # type: ignore
import fake_useragent as ua  # type: ignore
import filetype  # type: ignore
import requests

Number = Union[int, float]

_log = logging.getLogger("tankobon")

BS4_PARSER = "html5lib"  # if you want, change to lxml for faster parsing
USER_AGENT = ua.UserAgent()

RE_DOMAIN = re.compile(r"^(?:www\.)?(.*)(:(\d+))?$")

# all config/cache files are stored here.
ROOT = pathlib.Path.home() / ".local" / "share" / "tankobon"
ROOT.mkdir(parents=True, exist_ok=True)


def plural(n_items, noun):
    return f"{n_items} {noun}{'s' if n_items > 1 else ''}"


def filesize(content: bytes) -> str:
    """Create a human-readable filesize for content.

    Args:
        content: The bytes to get the size of.
    Returns:
        A string of the filesize ending in B, kB, etc.
    """
    filesize = float(len(content))
    for suffix in ["B", "KiB", "MiB", "GiB"]:
        if filesize < 1024.0 or suffix == "GiB":
            break
        filesize /= 1024.0
    return f"{filesize:.1f} {suffix}"


def _is_valid_char(char):
    return char.isalnum()


def sanitize(name: str) -> str:
    """Sanitise a name so it can be used as a filename.
    Args:
        name: The name to sanitise.
    Returns:
        The sanitised name as a string.
    """

    sanitised = "".join([c.lower() if _is_valid_char(c) else "_" for c in name])

    # remove duplicate underscores
    return re.sub("_{2,}", "_", sanitised).strip("_")


def soup(
    url: str, *args, session: Optional[requests.Session] = None, **kwargs
) -> bs4.BeautifulSoup:
    """Get a url as a BeautifulSoup.

    Args:
        url: The url to get a soup from.
        *args: Passed to session.get().
        session: The session to use to download the soup.
            Defaults to None.
        **kwargs: Passed to session.get().
    """

    if session is None:
        session = requests.Session()

    response = session.get(url, *args, **kwargs)

    return bs4.BeautifulSoup(response.text, BS4_PARSER)


def save_response(path: pathlib.Path, res: requests.models.Response) -> pathlib.Path:
    """Save a Requests response at path with the correct file extension.

    Args:
        path: The path where to save the file at.
        res: The response.

    Returns:
        The full path to the file.
    """

    path = path.with_suffix(f".{filetype.guess(res.content).extension}")
    with path.open("wb") as f:
        f.write(res.content)
    _log.debug(
        "saved response from %s at %s (%s)", res.url, path, filesize(res.content)
    )

    return path


def is_url(url: str) -> bool:
    """Check whether or not a string is a url."""
    result = urlparse(url)
    return all([result.scheme, result.netloc, result.path])


def parse_domain(url: str) -> str:
    """Parse out a url's domain.

    Args:
        url: The url to parse.

    Returns:
        The domain.
    """

    return RE_DOMAIN.findall(urlparse(url).netloc)[0][0]


class UserSession(requests.Session):
    """requests.Session with randomised user agent in the headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.headers.update({"User-Agent": USER_AGENT.random})


class PersistentDict(collections.UserDict):
    """A UserDict that can be loaded and dumped to disk persistently.
    (As long as the dictionary contents can be serialised to JSON.)

    Usage:

    ```python
    from tankobon.utils import PersistentDict

    file = "test.json"

    with PersistentDict(file) as d:
        d["foo"] = "bar"

    # '/where/to/save.json' now looks like this:
    # {
    #     "foo": "bar"
    # }

    # It can also be used without a context manager.
    # Just remember to close() it, or any changes won't be written to disk!

    d = PersistentDict(file)
    d["baz"] = 42
    d.close()
    ```
    """

    def __init__(
        self, path: Union[str, pathlib.Path], *args, compress: bool = False, **kwargs
    ):
        super().__init__(*args, **kwargs)

        if isinstance(path, str):
            path = pathlib.Path(path)

        self.path = path
        self.compress = compress

        try:
            if compress:
                f = gzip.open(self.path, "rt")
            else:
                f = self.path.open()

            self.data.update(json.load(f))

            f.close()

        except FileNotFoundError:
            pass

    def close(self):
        if self.compress:
            f = gzip.open(self.path, "wt")
        else:
            f = self.path.open("w")

        json.dump(self.data, f, indent=2)
        f.close()

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()


class Config(PersistentDict):

    CONFIG = "config.json"
    DEFAULTS = {"lang": "en"}

    def __init__(self, path: Optional[pathlib.Path] = None):
        if path is None:
            path = ROOT / self.CONFIG

        super().__init__(path, compress=False, **self.DEFAULTS)

    def __getitem__(self, key):
        if key not in self:
            super().__setitem__(key, os.environ[f"TANKOBON_{key.upper()}"])

        return super().__getitem__(key)
