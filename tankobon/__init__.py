# coding: utf8
"""Yet another manga downloader.

.. include:: ./documentation.md
"""

from .__version__ import __version__

from .core import Cache, Downloader
from .sources.base import Parser
