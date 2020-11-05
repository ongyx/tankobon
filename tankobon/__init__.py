# coding: utf8
"""Manga browser/downloader."""

import logging

import coloredlogs

from .__version__ import __version__  # noqa: f401

coloredlogs.install(
    fmt=" %(levelname)-8s :: %(message)s",
    logger=logging.getLogger("tankobon"),
)
