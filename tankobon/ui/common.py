# coding: utf8
"""common functions shared by the UI."""

from typing import List

from .. import iso639


def describe_langs(langs: List[str]):
    return [
        f"{iso639.DATASET[lang].native_name if lang in iso639.DATASET else '???'} ({lang})"
        for lang in langs
    ]
