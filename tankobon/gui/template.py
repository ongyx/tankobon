# coding: utf8
"""This template generates the HTML view for a manga."""

import string

from PySide6.QtWidgets import QTextEdit

from ..models import Manga

from .utils import resource

TEMPLATE = string.Template(resource(":/view.html").decode("utf8"))


def create(manga: Manga):
    # convert table to html from markdown
    textedit = QTextEdit()
    textedit.setMarkdown(manga.summary())

    table = textedit.toHtml()

    return TEMPLATE.substitute(
        url=manga.meta.url, title=manga.meta.title, desc=manga.meta.desc, table=table
    )
