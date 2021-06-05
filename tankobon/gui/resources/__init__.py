# coding: utf8
"""On-the-fly resource loading for the GUI (logos, etc.)"""

import io
import pathlib
import shutil
import zipfile

import requests
from PySide6.QtGui import QPixmap

PATH = pathlib.Path(__file__).parent

PIXMAPS = {"logo": "logo.jpg", "missing": "missing.jpg"}


def pixmap(name):
    return QPixmap(str(PATH / PIXMAPS[name]))


def view_css():
    return (PATH / "view.css").read_text()


def view_html():
    return (PATH / "view.html").read_text()
