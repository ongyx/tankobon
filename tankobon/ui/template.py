# coding: utf8
"""This template generates the HTML view for a manga."""

import bbcode  # type: ignore

from ..models import Manga

BBCODE = bbcode.Parser(drop_unrecognized=True)

# Extend BBCode syntax to support more compilcated tags.

# Markdown-style lists (without explicit [list][/list]).
BBCODE.add_simple_formatter("*", "&#8226; %(value)s <br>", newline_closes=True)


def create(manga: Manga, lang: str):
    # fallback to english if localised description is not available.
    desc = manga.meta.desc.get(lang) or manga.meta.desc["en"]

    return BBCODE.format(desc).replace("\n", "<br>")
