# coding: utf8
"""Core functionality of tankobon."""

from __future__ import annotations

import abc
import concurrent.futures as cfutures
import functools
import hashlib
import json
import logging
import pathlib
import shutil
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Union

import bs4
import requests
import fake_useragent as ua

from . import utils
from .exceptions import MangaNotFoundError, PagesNotFoundError, UnknownDomainError

# monkey-patch json for indent
json.dump = functools.partial(json.dump, indent=4)
json.dumps = functools.partial(json.dumps, indent=4)

# type hints
StrList = Optional[List[str]]

_log = logging.getLogger("tankobon")

BS4_PARSER = "html5lib"
USER_AGENT = ua.UserAgent()

CACHE_PATH = pathlib.Path.home() / ".tankobon"
CACHE_PATH.mkdir(exist_ok=True)

# index at the root of the cache
INDEX_FILE = "index.json"

# Each manga has a unique hash name generated using MD5
# (see Metadata.hash).
# This hash name is used to create a per-manga directory (to store this file and the manga pages).
CHAPTER_FILE = "chapters.json"


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

    _hash: str = ""

    def __post_init__(self):
        if self.genres is not None:
            self.genres = [utils.sanitize(g.strip()) for g in self.genres]

        self.desc = self.desc.strip()

    def parsed(self):
        """Check whether the metadata fields has been partially/totally filled."""
        return any(value for key, value in self.__dict__.items() if key != "url")

    @property
    def hash(self):
        if not self._hash:
            self._hash = hashlib.md5((self.title + self.url).encode()).hexdigest()

        return self._hash


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
        data: A map of chapter id to the Chapter object.
        domain: The name of the manga host website, i.e 'mangadex.org'.
            This **must** be set in any derived subclasses like so:

            class MyManga(Manga):
                domain = 'mymanga.com'
                ...

        hash: A MD5 checksum of the manga title + url.
            This can be used to uniquely identify manga.
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

        self.data: Dict[str, Chapter] = {}

        chapters = data.get("chapters")

        if chapters is not None:
            self.data = {cid: Chapter(**cdata) for cid, cdata in chapters.items()}

    @classmethod
    def parser(cls, url: str):
        """Get the appropiate subclass for the domain in url.

        Args:
            url: The url to get the subclass for.

        Returns:
            The subclass that can be used to parse the url.

        Raises:
            UnknownDomainError, if there is no registered subclass for the url domain.
        """

        domain = utils.parse_domain(url)

        try:
            subclass = cls.registered[domain]
        except KeyError:
            raise UnknownDomainError(f"no parser found for domain '{domain}'")

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
            "chapters": {cid: cdata.__dict__ for cid, cdata in self.data.items()},
        }

    def refresh(self, pages: bool = False):
        """Refresh the list of chapters available.

        Args:
            pages: Whether or not to parse the pages for any new chapters.
                Defaults to False (may take up a lot of bandwidth for many chapters).
        """

        self.meta = self.metadata()

        for chapter in self.chapters():

            if chapter.id not in self.data:

                _log.info("manga: adding new chapter %s", chapter.id)

                self.data[chapter.id] = chapter

            else:
                # take the reference to the existing chapter so assigning pages will work properly.
                chapter = self.data[chapter.id]

            if pages and chapter.pages is None:

                _log.info("manga: adding pages to chapter %s", chapter.id)

                self.data[chapter.id].pages = self.pages(chapter)

    def soup_from_url(self, url: str) -> bs4.BeautifulSoup:
        """Retreive a url and create a soup using its content."""
        return bs4.BeautifulSoup(self.session.get(url).text, BS4_PARSER)

    def download(self, cid: str, to: Union[str, pathlib.Path]) -> List[pathlib.Path]:
        """Download a chapter's pages to a folder.

        Args:
            cid: The chapter id to download.
            to: The folder to download the pages to.

        Returns:
            A list of absolute paths to the downloaded pages in ascending order
            (1.png, 2.png, 3.png, etc.)

        Raises:
            PagesNotFoundError, if the chapter's pages have not been parsed yet.
            To avoid this, .pages(refresh=True) should be called at least once.
        """

        to = pathlib.Path(to)

        paths = []

        chapter = self.data[cid]

        if chapter.pages is None:
            raise PagesNotFoundError(
                f"chapter {cid} has no pages (did you forget to call .refresh(pages=True)?)"
            )

        total = len(chapter.pages)

        with cfutures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(self.session.get, url): count
                for count, url in enumerate(chapter.pages)
            }

            for future in cfutures.as_completed(futures):
                count = futures[future]

                _log.info(f"manga: [{chapter.id}] downloading page {count} of {total}")

                resp = future.result()
                path = utils.save_response(to / str(count), resp)
                paths.append(path)

        return paths

    def download_cover(self) -> requests.Response:
        """Download the manga cover.
        The manga cover url must be valid.

        Returns:
            The requests.Response of the manga cover url.
        """

        return self.session.get(self.meta.cover)

    def total(self) -> int:
        """Return the total number of pages in this manga.
        All the chapter pages must have already been parsed.
        """

        return sum(
            len(c.pages) if c.pages is not None else 0 for c in self.data.values()
        )

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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.registered[cls.domain] = cls

    def __getattr__(self, attr):
        try:
            return self.meta.__dict__[attr]
        except KeyError:
            raise AttributeError

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()


class Cache:
    def __init__(self, path: pathlib.Path = CACHE_PATH):
        self.path = path
        self.path.mkdir(exist_ok=True)

        self.index_path = self.path / INDEX_FILE

        # The index maps manga urls to their metadata.
        try:
            with self.index_path.open() as f:
                self.index = json.load(f)

        except FileNotFoundError:
            _log.info("cache: index not found, creating")
            self.index = {}

    def _hash_name(self, url):
        return self.index[url]["_hash"]

    def _hash_path(self, url):
        return self.path / self._hash_name(url)

    def save(self, manga: Manga, cover: bool = False):
        """Save this manga within the cache.

        Args:
            manga: The manga object to save.
            cover: Whether or not to save the cover to the cache (if the cover url exists).
                Defaults to False.
        """

        # make sure hash is generated
        manga.meta.hash

        export = manga.export_dict()

        metadata = export["metadata"]
        chapters = export["chapters"]

        # Save only metadata in the index for faster loading.
        # Chapters are saved in another json file.
        self.index[manga.url] = metadata

        manga_path = self._hash_path(manga.url)
        manga_path.mkdir(exist_ok=True)

        with (manga_path / CHAPTER_FILE).open("w") as f:
            json.dump(chapters, f)

        if cover and manga.meta.cover:
            utils.save_response(manga_path / "cover", manga.download_cover())

    def load(self, url: str):
        """Load a manga by url.

        Args:
            url: The manga url.

        Returns:
            The Manga object.

        Raises:
            MangaNotFoundError, if the manga does not exist in the cache.
        """
        if url not in self.index:
            raise MangaNotFoundError(
                f"{url} does not exist in cache. Did you try to create it? (Use Manga.from_url(url) instead.)"
            )

        with (self._hash_path(url) / CHAPTER_FILE).open() as f:
            chapters = json.load(f)

        return Manga.import_dict({"metadata": self.index[url], "chapters": chapters})

    def delete(self, url: str):
        """Delete a manga from the cache.

        Args:
            url: The manga url.

        Raises:
            MangaNotFoundError, if the manga does not exist in the cache.
        """
        if url not in self.index:
            raise MangaNotFoundError(f"can't delete {url}")

        shutil.rmtree(self._hash_path(url))
        del self.index[url]

    def close(self):
        with self.index_path.open("w") as f:
            json.dump(self.index, f, indent=2)

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()
