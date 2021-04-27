# coding: utf8
"""Utilities for tankobon."""

import logging
import pathlib
import re
from typing import Optional, Union
from urllib.parse import urlparse

import bs4  # type: ignore
import filetype  # type: ignore
import requests

Number = Union[int, float]

_log = logging.getLogger("tankobon")

# Downloader config
BSOUP_PARSER = "html5lib"  # if you want, change to lxml for faster parsing
TIMEOUT = 15
COOLDOWN = 2

RE_DOMAIN = re.compile(r"^(?:www\.)?(.*)(:(\d+))?$")


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


def get_soup(
    *args,
    encoding: Optional[str] = None,
    parser: str = BSOUP_PARSER,
    session: Optional[requests.Session] = None,
    **kwargs,
) -> bs4.BeautifulSoup:
    """Get a url as a BeautifulSoup.

    Args:
        *args: See get_url.
        encoding: The encoding to decode.
            Defaults to the autodetected encoding (by requests).
        parser: The parser to use.
            Must be 'html.parser', 'html5lib' or 'lxml'.
        session: The session to use to download the soup.
            Defaults to None.
        **kwargs: See get_url.
    """

    if session is not None:
        response = session.get(*args, **kwargs)
    else:
        response = requests.get(*args, **kwargs)

    if encoding is not None:
        html_text = response.content.decode(encoding)
    else:
        html_text = response.text

    return bs4.BeautifulSoup(html_text, parser)


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


class TimedSession(requests.Session):
    def get(self, *args, **kwargs):
        return super().get(*args, timeout=TIMEOUT, **kwargs)


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
