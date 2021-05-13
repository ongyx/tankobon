# coding: utf8
"""This template generates the HTML view for a manga."""

import string

from ..core import Manga
from ..cli import _info_table

TEMPLATE = string.Template(
    """
# *$title*

---

From Weebipedia, the free encyclopedia

$desc

## Volumes

$table
"""
)


def create(manga: Manga):
    return TEMPLATE.substitute(
        title=manga.meta.title, desc=manga.meta.desc, table=_info_table(manga)[0]
    )
