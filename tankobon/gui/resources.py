# coding: utf8
"""On-the-fly resource loading for the GUI (logos, etc.)"""

import io
import shutil
import zipfile

import requests
from PySide6.QtGui import QPixmap

from .. import core
from ..__version__ import __version__

PATH = core.CACHE_PATH / "resources"

FLAG = PATH / ".downloaded"
URL = "https://raw.githubusercontent.com/ongyx/tankobon/master/resources.zip"


PIXMAPS = {"logo": "logo.jpg", "missing": "missing.jpg"}


def _init():
    try:
        old_version = FLAG.read_text()
    except FileNotFoundError:
        old_version = ""

    if old_version != __version__:

        if PATH.is_dir():
            shutil.rmtree(str(PATH))
            PATH.mkdir()

        with requests.get(URL) as resp:
            buf = io.BytesIO(resp.content)

            with zipfile.ZipFile(buf) as zf:
                zf.extractall(path=PATH)

        FLAG.write_text(__version__)


_init()


def pixmap(name):
    return QPixmap(str(PATH / PIXMAPS[name]))


def view_css():
    return (PATH / "view.css").read_text()


def view_html():
    return (PATH / "view.html").read_text()
