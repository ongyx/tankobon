# coding: utf8
"""On-the-fly resource loading for the GUI (logos, etc.)"""

import io
import zipfile

import requests
from PySide6.QtGui import QPixmap

from . import core

PATH = core.CACHE_PATH / "resources"
PATH.mkdir(exist_ok=True)

FLAG = PATH / ".downloaded"
URL = "https://raw.githubusercontent.com/ongyx/tankobon/master/resources.zip"


PIXMAPS = {"logo": "logo.jpg", "missing": "missing.jpg"}


def _init():
    if not FLAG.exists():
        with requests.get(URL) as resp:
            buf = io.BytesIO(resp.content)

            with zipfile.ZipFile(buf) as zf:
                zf.extractall(path=PATH)

        FLAG.touch()


_init()


def pixmap(name):
    return QPixmap(str(PATH / PIXMAPS[name]))
