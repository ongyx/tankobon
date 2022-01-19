# coding: utf8
"""Yet another manga downloader."""

from .__version__ import __version__

from .core import Cache, Downloader
from .sources.base import Parser

__pdoc__ = {"ui": False}
