# coding: utf8
"""Utilities for tankobon.
"""

import pathlib
import re
from typing import Union, Optional

import bs4
import filetype
import requests
import requests_random_user_agent  # noqa: F401

Number = Union[int, float]

# Downloader config
BSOUP_PARSER = "html5lib"  # if you want, change to lxml for faster parsing
TIMEOUT = 5
COOLDOWN = 0.5
THREADS = 8

# map to mimetypes (mimetypes module sucks)
FILE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
}


def get_file_extension(response: requests.models.Response) -> str:
    """Get a extension from a response by parsing its mimetype.

    Args:
        response: The response object (from requests.get, et al.)
    """

    # FIXME: this code breaks if header is incorrect
    # content_type = response.headers.get("Content-Type")
    # if content_type is not None:
    #    ext = FILE_EXTENSIONS[content_type.partition(";")[0]]
    # else:
    #    ext = response.url.rpartition(".")[-1]

    return f".{FILE_EXTENSIONS[filetype.guess_mime(response.content)]}"


def _is_valid_char(char):
    return char.isalnum()


def sanitize_filename(name: str) -> str:
    """Sanitise a name so it can be used as a filename.
    Args:
        name: The name to sanitise.
    Returns:
        The sanitised name as a string.
    """

    sanitised = "".join([c if _is_valid_char(c) else "_" for c in name])

    # remove duplicate underscores
    return re.sub("_{2,}", "_", sanitised)


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

    path = path.with_suffix(get_file_extension(res))
    with path.open("wb") as f:
        f.write(res.content)

    return path