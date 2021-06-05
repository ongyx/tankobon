# coding: utf8
"""This template generates the HTML view for a manga."""

import string

from PySide6.QtWidgets import QTextEdit

from ..core import Manga
from ..cli import _info_table

from .utils import resource

TEMPLATE = string.Template(resource(":/view.html").decode("utf8"))


def create(manga: Manga):
    # convert table to html from markdown
    textedit = QTextEdit()
    textedit.setMarkdown(_info_table(manga)[0])

    table = textedit.toHtml()

    return TEMPLATE.substitute(
        title=manga.meta.title, desc=manga.meta.desc, table=table
    )
