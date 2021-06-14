# coding: utf8
"""Model classes."""

from __future__ import annotations

import collections
import hashlib
import logging
from typing import cast, Any, Dict, List, Optional

import natsort  # type: ignore

from . import utils
from .jsonclasses import dataclass, field


# cast because mypy keeps complaining about generic types
def _list():
    return cast(List[Any], field(default_factory=list))


def _dict():
    return cast(Dict[str, Any], field(default_factory=dict))


_log = logging.getLogger("tankobon")


@dataclass
class Metadata:
    """Metadata for a manga.

    Args:
        url: The url to the manga title page.
        title: The manga name in English (romanized/translated).
        alt_titles: A list of alternative names for the manga.
            i.e in another language, original Japanese name, etc.
        desc: The sypnosis (human-readable info) of the manga.
        cover: The url to the manga cover page (must be an image).
        authors: A list of author names.
        genres: A list of catagories the manga belongs to.
            i.e shounen, slice_of_life, etc.
            Note that the catagories are sanitised using utils.sanitise() on initalisation.
        other: Miscellanious map of keys to values.
            May be used by parsers to store parser-specific info (keep state).

    Attributes:
        hash: A SHA-256 checksum of the manga url.
            (Can be used for filename-safe manga storage.)
    """

    url: str
    title: str = ""

    alt_titles: List[str] = _list()

    desc: str = ""
    cover: str = ""

    authors: List[str] = _list()
    genres: List[str] = _list()

    hash: str = ""

    other: Dict[str, Any] = _dict()

    def __post_init__(self):
        if self.genres:
            self.genres = [utils.sanitize(g.strip()) for g in self.genres]

        self.desc = self.desc.strip().replace("\r\n", "\n")

        if not self.hash:
            self.hash = hashlib.sha256(self.url.encode()).hexdigest()


@dataclass
class Chapter:
    """A manga chapter.

    Args:
        id: The chapter id as a string (i.e 1, 2, 10a, etc.).
        url: The chapter url.
        title: The chapter name.
        volume: The volume the chapter belongs to.
        lang: The ISO 639-1 language code that this chapter was translated to.
        pages: A list of image urls to the chapter pages.
        other: Miscellanious map of keys to values.
            May be used by parsers to store parser-specific info (keep state).
    """

    id: str
    url: str
    title: str = ""
    volume: str = "0"
    lang: str = "en"

    pages: List[str] = _list()

    other: Dict[str, Any] = _dict()


class Manga:
    """A manga.

    Selecting chapters in this manga can be done by slicing:

    manga[start_cid:end_cid:lang]  # returns a list of Chapter objects

    where start_cid is the first chapter of the selection, and end_cid is the last chapter of the selection.
    lang is the ISO 639-1 language code of the chapters to select. i.e:

    # Select chapters 1 to 5 in the Spanish language (inclusive of chapter 5).
    # NOTE: If the chapter does not have a translation for the selected language,
    # the number of chapters you get may not be the number requested!
    chapters = manga["1":"5":"es"]

    Args:
        meta: The manga metadata.
        chapters: The manga chapters.

    Attributes:
        chapters: A map of chapter ids to a map of ISO 639-1 language codes to Chapter objects (chapters may have several languages):

            {
                // chapter id
                "1": {
                    // ISO 639-1 language code
                    "en": Chapter(...)
                }
            }

        info: A dictionary which has the following keys:

            chapters (int)
                The total number of chapters across all languages.

            volumes (set)
                The volumes that this manga has across all languages.

            langs (set)
                ISO 639-1 language codes that this manga was translated to.
                Note that chapters may not have a translation for all language codes.
    """

    def __init__(
        self,
        metadata: Metadata,
        chapters: Optional[dict] = None,
    ):
        self.meta = metadata

        self.chapters: Dict[str, Dict[str, Chapter]]

        self.chapters = collections.defaultdict(dict)

        if chapters is not None:
            self.chapters.update(chapters)

    @property
    def info(self):
        info = {
            "chapters": 0,
            "volumes": set(),
            "langs": set(),
        }

        for cid, langs in self.chapters.items():
            info["langs"].update(langs.keys())

            for chapter in langs.values():
                info["chapters"] += 1
                info["volumes"].add(chapter.volume)

        return info

    def add(self, chapter: Chapter):
        """Add a chapter to this manga.
        The chapter will not be added if it already exists (has the same id and lang as the existing one).

        Args:
            chapter: The chapter to add.
        """

        if not self.exists(chapter):
            self.chapters[chapter.id][chapter.lang] = chapter

    def remove(self, cid: str, lang: str = "en") -> Chapter:
        """Remove a chapter from this manga.

        Args:
            cid: The chapter id to remove.
            lang: The chapter language to remove.
                Defaults to 'en'.

        Returns:
            The removed chapter.
        """

        return self.chapters[cid].pop(lang)

    def exists(self, chapter: Chapter) -> bool:
        """Check whether a chapter already exists in this manga.

        Args:
            chapter: The chapter object.

        Returns:
            True if it exists, otherwise False.
        """

        langs = self.chapters.get(chapter.id, {})

        return bool(langs) and chapter.lang in langs

    def dump(self) -> dict:
        """Serialise this manga to a dict."""
        return {"meta": self.meta, "chapters": self.chapters}

    @classmethod
    def load(cls, data: dict) -> Manga:
        """Deserialise this manga from a dict.

        Args:
            data: The serialised manga.

        Returns:
            The Manga object.
        """
        return cls(data["meta"], chapters=data["chapters"])  # type: ignore

    def summary(self, lang: str = "en") -> str:
        """Create a Markdown table summary of all volumes and chapters in this manga.

        Args:
            lang: The language to summerise for.

        Returns:
            The Markdown table as a string.
        """

        table = ["| volume | chapter | title ", "|--------|---------|-------"]

        for cid, langs in natsort.natsorted(self.chapters.items()):

            chapter: Chapter = langs.get(lang)

            if chapter is None:
                # chapter does not have the language.
                continue

            table.append(
                "| {:<6} | {:<7} | [{}]({})".format(
                    chapter.volume or "(empty)",
                    chapter.id or "(empty)",
                    chapter.title or "(empty)",
                    chapter.url,
                )
            )

        return "\n".join(table)

    def select(self, cids: str, lang: str = "en") -> List[Chapter]:
        """Select chapters from this manga.

        Args:
            cids: A list of chapter ids as a string, delimited by a comma.
                Ranges are also valid (1-5).
                i.e '1,3,5,8-10' (select chapters 1,3,5 and 8-10 inclusive of 10).
            lang: The language of the chapters.
                Note that if a chapter does not have the language requested, it will be skipped.

        Returns:
            A list of Chapter objects.
        """

        chapters = []

        for cid in cids.split(","):

            if "-" in cid:
                start, end = cid.split("-")
                chapters.extend(self[start:end:lang])  # type: ignore

            else:
                langs = self.chapters[cid]
                chapter = langs.get(lang)

                if chapter is not None:
                    chapters.append(chapter)

        return chapters

    def parsed(self) -> bool:
        """Check whether this manga has been parsed (has at least one chapter)."""
        return len(self.chapters) >= 1

    def __getitem__(self, key):
        if isinstance(key, slice):
            sorted_chapters = natsort.natsorted(self.chapters.keys())

            try:
                start = sorted_chapters.index(key.start)
                if key.stop is not None:
                    # include the last chapter also
                    stop = sorted_chapters.index(key.stop, start) + 1
                else:
                    stop = len(sorted_chapters)
            except ValueError:
                return []

            lang = "en" if key.step is None else key.step

            return [
                self.chapters[c][lang]
                for c in sorted_chapters[start:stop]
                if lang in self.chapters[c]
            ]

        else:
            return self.chapters[key]

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()
