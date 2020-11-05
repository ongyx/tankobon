# coding: utf8
"""Utilities for tankobon.
"""

import random
import re
from typing import Union, Optional

import bs4
import requests
import requests_random_user_agent

Number = Union[int, float]

# Downloader config
BSOUP_PARSER = "html5lib"  # if you want, change to lxml for faster parsing
TIMEOUT = 5
COOLDOWN = 0.5
THREADS = 8

# map to mimetypes (mimetypes module sucks)
FILE_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif"}


def get_file_extension(response: requests.models.Response) -> str:
    """Get a extension from a response by parsing its mimetype.

    Args:
        response: The response object (from requests.get, et al.)
    """

    content_type = response.headers["Content-Type"]
    return f".{FILE_EXTENSIONS[content_type]}"


def get_url(url: str, timeout: Number = TIMEOUT) -> requests.models.Response:
    """Retrieve a URL.

    Args:
        url: The url to retrieve.
        timeout: How long to wait for a server response.

    Returns:
        The response of the URL.

    Raises:
        ValueError, if the webpage could not be fetched.
        IndexError, if the connection timed out.
    """

    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.exceptions.HTTPError as err:
        raise ValueError(f"failed to fetch webpage: {err}")
    except requests.exceptions.Timeout:
        raise IndexError(f"server timed out: {TIMEOUT} seconds without response")

    return response


def get_soup(
    *args, encoding: Optional[str] = None, parser: str = BSOUP_PARSER, **kwargs
) -> bs4.BeautifulSoup:
    """Get a url as a BeautifulSoup.

    Args:
        *args: See get_url.
        encoding: The encoding to decode.
            Defaults to the autodetected encoding (by requests).
        parser: The parser to use.
            Must be 'html.parser', 'html5lib' or 'lxml'.
        **kwargs: See get_url.
    """

    response = get_url(*args, **kwargs)
    if encoding is not None:
        html_text = response.content.decode(encoding)
    else:
        html_text = response.text

    return bs4.BeautifulSoup(html_text, parser)
