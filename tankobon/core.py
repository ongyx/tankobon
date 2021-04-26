# coding: utf8

from __future__ import annotations

import abc
import hashlib
import json
import logging
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, Generator, IO, List, Optional

import bs4
import requests
import fake_useragent as ua

from . import utils
from .exceptions import CacheError

# type hints
StrList = Optional[List[str]]

_log = logging.getLogger("tankobon")

BS4_PARSER = "html5lib"
USER_AGENT = ua.UserAgent()

CACHE_PATH = pathlib.Path.home() / ".tankobon"
INDEX_PATH = "index.json"


@dataclass
class Metadata:
    """Helper class to store manga metadata.

    Args:
        url: The url to the manga title page.
        title: The manga name in English (romanized/translated).
        alt_titles: A list of alternative names for the manga.
            i.e in another language, original Japanese name, etc.
        authors: A list of author names.
        genres: A list of catagories the manga belongs to.
            i.e shounen, slice_of_life, etc.
            Note that the catagories are sanitised using utils.sanitise() on initalisation.
        desc: The sypnosis (human-readable info) of the manga.
        cover: The url to the manga cover page (must be an image).
    """

    url: str
    title: str = ""

    alt_titles: StrList = None
    authors: StrList = None
    genres: StrList = None

    desc: str = ""
    cover: str = ""

    def __post_init__(self):
        if self.genres is not None:
            self.genres = [utils.sanitize(g.strip()) for g in self.genres]

    def parsed(self):
        """Check whether the metadata fields has been partially/totally filled."""
        return any(value for key, value in self.__dict__.items() if key != "url")


@dataclass
class Chapter:
    """A manga chapter.

    Args:
        id: The chapter id as a string (i.e 1, 2, 10a, etc.).
        url: The chapter url.
        title: The chapter name.
        volume: The volume the chapter belongs to.
        pages: A list of image urls to the chapter pages.
    """

    id: str
    url: str
    title: str = ""
    volume: str = "0"
    pages: StrList = None


class Manga(abc.ABC):
    """A manga hosted somewhere online.

    Attributes:
        chapter_data: A map of chapter id to the Chapter object.
        domain: The name of the manga host website, i.e 'mangadex.org'.
            This **must** be set in any derived subclasses like so:

            class MyManga(Manga):
                domain = 'mymanga.com'
                ...

        meta: The manga metadata as a Metadata object.
        registered: A map of subclass domain to the subclass itself.
            Subclasses can then be delegated to depending on a url's domain.
        session: The requests.Session used to download soups.
        soup: The BeautifulSoup of the manga title page.
    """

    # It might seem like a bad idea to have a mutable class attribute,
    # but it is intended to be shared across all class instances.
    # This allows subclasses to be registered.
    registered: Dict[str, Dict] = {}

    def __init__(self, data: Dict[str, Any]):
        self.meta = Metadata(**data["metadata"])

        self.session = requests.Session()
        self.session.headers.update(
            {"Referer": self.meta.url, "User-Agent": USER_AGENT.random}
        )

        self.soup = self.soup_from_url(self.meta.url)

        if not self.meta.parsed():
            self.meta = self.metadata()

        self.chapter_data: Dict[str, Chapter] = {}

        chapters = data.get("chapters")

        if chapters is not None:
            self.chapter_data = {
                cid: Chapter(**cdata) for cid, cdata in chapters.items()
            }

    @classmethod
    def parser(cls, url: str):
        """Get the appropiate subclass for the domain in url.

        Args:
            url: The url to get the subclass for.

        Returns:
            The subclass that can be used to parse the url.

        Raises:
            ValueError, if there is no registered subclass for the url domain.
        """

        domain = utils.parse_domain(url)

        try:
            subclass = cls.registered[domain]
        except KeyError:
            raise ValueError(f"no Manga subclass registered for {domain}")

        return subclass

    @classmethod
    def from_url(cls, url: str) -> Manga:
        """Parse a url into a Manga object.
        The appropiate subclass will be selected based on the url domain.

        Args:
            url: The url to parse.

        Returns:
            The parsed Manga object.
        """

        return cls.import_dict({"metadata": {"url": url}})

    @classmethod
    def import_dict(cls, data: Dict[str, Any]) -> Manga:
        """Import manga data.

        Args:
            data: The previously exported data from export_dict().
        """

        subclass = cls.parser(data["metadata"]["url"])
        return subclass(data)

    @classmethod
    def import_file(cls, file: [str, pathlib.Path, IO]) -> Manga:
        """Import manga data from a file."""

        if isinstance(file, (str, pathlib.Path)):
            file = open(file, "r")

        data = json.load(file)
        return cls.import_dict(data)

    def close(self):
        self.session.close()
        self.soup.decompose()

    def export_dict(self) -> Dict[str, Any]:
        """Export the manga data.
        The dict can be saved to disk and loaded back later using import_dict().

        Returns:
            The manga data as a dict.
        """

        return {
            "metadata": self.meta.__dict__,
            "chapters": {
                cid: cdata.__dict__ for cid, cdata in self.chapter_data.items()
            },
        }

    def export_file(self, file: [str, pathlib.Path, IO]):
        """Export the manga data to a file."""

        if isinstance(file, (str, pathlib.Path)):
            file = open(file, "w")

        json.dump(self.export_dict(), file, indent=4)

    def refresh(self, pages: bool = False):
        """Refresh the list of chapters available.

        Args:
            pages: Whether or not to parse the pages for any new chapters.
                Defaults to False (may take up a lot of bandwidth for many chapters).
        """

        for chapter in self.chapters():

            if chapter.id not in self.chapter_data:

                _log.info("adding new chapter %s", chapter.id)

                self.chapter_data[chapter.id] = chapter

            else:
                # take the reference to the existing chapter so assigning pages will work properly.
                chapter = self.chapter_data[chapter.id]

            if pages and chapter.pages is None:

                _log.info("adding pages to chapter %s", chapter.id)

                self.chapter_data[chapter.id].pages = self.pages(chapter)

    def soup_from_url(self, url: str) -> bs4.BeautifulSoup:
        """Retreive a url and create a soup using its content."""
        return bs4.BeautifulSoup(self.session.get(url).text, BS4_PARSER)

    @abc.abstractmethod
    def metadata(self) -> Metadata:
        """Parse metadata from the manga title page.

        Returns:
            A Metadata object.
        """

    @abc.abstractmethod
    def chapters(self) -> Generator[Chapter, None, None]:
        """Parse chapter info from the manga title page.

        Yields:
            A Chapter object for each chapter in the manga.
        """

    @abc.abstractmethod
    def pages(self, chapter: Chapter) -> List[str]:
        """Parse pages (images of the manga) from the manga chapter page.

        Args:
            chapter: The Chapter object to parse for.

        Returns:
            A list of urls to the chapter pages (must be images).
        """

    @property
    @abc.abstractmethod
    def domain(self) -> str:
        pass

    def __getattr__(self, attr):
        if attr in self.meta.__dict__:
            return self.meta.__dict__[attr]

        return object.__getattr__(self, attr)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.registered[cls.domain] = cls

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()


class Cache:
    def __init__(self, path: pathlib.Path = CACHE_PATH):
        self.path = path
        self.path.mkdir(exist_ok=True)

        self.index_path = self.path / INDEX_PATH

        # The index maps manga urls to their hashnames (used as filenames).
        # The hashname only has to be calculated once.
        try:
            with self.index_path.open() as f:
                self.index = json.load(f)

        except FileNotFoundError:
            self.index = {}

    def _hashname(self, manga):
        return self.index.setdefault(
            manga.url, hashlib.md5((manga.title + manga.url).encode()).hexdigest()
        )

    def _hashpath(self, manga):
        return self.path / f"{self._hashname(manga)}.json"

    def exists(self, url: str) -> bool:
        """Check whether the manga url is in the cache."""
        return url in self.index

    def load(self, url: str) -> Manga:
        """Load a manga by url.

        Args:
            url: The manga url.

        Returns:
            The Manga object.

        Raises:
            CacheError, if the manga does not exist in the cache.
        """
        if not self.exists(url):
            raise CacheError(
                f"manga {url} does not exist in cache. Did you try to create it? (Use Manga.from_url(url) instead.)"
            )

        return Manga.import_file(self.path / f"{self.index[url]}.json")

    def save(self, manga: Manga):
        """Save a manga to the cache.

        Args:
            manga: The manga to save.
        """
        # so we don't have to use a sanitised filename, which may collide.
        manga.export_file(self._hashpath(manga))

    def delete(self, url: str):
        """Delete a manga from the cache.

        Args:
            url: The manga url.

        Raises:
            CacheError, if the manga does not exist in the cache.
        """
        if not self.exists(url):
            raise CacheError(f"can't delete non-existant manga {url}")

        hashname = self.index.pop(url)
        (self.path / f"{hashname}.json").unlink()

    def close(self):
        with self.index_path.open("w") as f:
            json.dump(self.index, f, indent=2)

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()
