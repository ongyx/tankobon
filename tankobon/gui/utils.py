# coding: utf8

from PySide6.QtCore import QResource
from PySide6.QtGui import QColor


def resource(path: str) -> bytes:
    return QResource(path).data().tobytes()  # type: ignore


def is_dark(color: QColor) -> bool:
    hex_color = color.name().lstrip("#")
    colors = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
    return [color < 0x7F for color in colors].count(True) >= 2
