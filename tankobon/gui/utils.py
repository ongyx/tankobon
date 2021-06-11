# coding: utf8

import os
import platform
import subprocess

from PySide6.QtCore import QResource
from PySide6.QtGui import QColor

SYSTEM = platform.system()


def resource(path: str) -> bytes:
    return QResource(path).data().tobytes()  # type: ignore


def is_dark(color: QColor) -> bool:
    hex_color = color.name().lstrip("#")
    colors = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
    return [color < 0x7F for color in colors].count(True) >= 2


def xopen(path: str):
    """Open a path using the correct application.

    Args:
        path: The path to open.
    """

    if SYSTEM == "Windows":
        os.startfile(path)  # type: ignore
    elif SYSTEM == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])
