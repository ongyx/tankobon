# coding: utf8
"""Core functionality of tankobon."""

from __future__ import annotations

import abc
import concurrent.futures as cfutures
import hashlib
import json
import logging
import pathlib
import re
import shutil
from dataclasses import dataclass
from typing import cast, Any, Callable, Dict, Generator, List, Optional, Type, Union

import bs4  # type: ignore
import requests
import fake_useragent as ua  # type: ignore
from natsort import natsorted  # type: ignore

from . import utils
from .exceptions import MangaNotFoundError, PagesNotFoundError, UnknownDomainError

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
# This hash name is used to create a per-manga directory (to store the manga pages).


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

        domain: The regex of the manga url as a string.
            This is used to determine whether this class is suitable for parsing a manga url.
            It must be set in any subclasses:

            class MyManga(tankobon.core.Manga):

                domain = r"my-manga-host.com"

        hash: A MD5 checksum of the manga title + url.
            This can be used to uniquely identify manga.

        meta: The manga metadata as a Metadata object.

        registered: A list of Manga subclasses
            (Subclasses are automatically registered.)

        session: The requests.Session used to download soups.

        soup: The BeautifulSoup of the manga title page.
    """

    # This allows subclasses to be registered.
    registered: List[Type[Manga]] = []

    def __init__(self, data: Dict[str, Any]):
        self.meta = Metadata(**data["metadata"])

        self.session = requests.Session()
        self.session.headers.update(
            {"Referer": self.meta.url, "User-Agent": USER_AGENT.random}
        )

        self._soup = None

        self.data: Dict[str, Chapter] = {}

        chapters = data.get("chapters")

        if chapters is not None:
            self.data = {cid: Chapter(**cdata) for cid, cdata in chapters.items()}

    @property
    def soup(self):
        if self._soup is None:
            self._soup = self.soup_from_url(self.meta.url)

        return self._soup

    @classmethod
    def parser(cls, url: str) -> Type[Manga]:
        """Get the appropiate subclass for the domain in url.

        Args:
            url: The url to get the subclass for.

        Returns:
            The subclass that can be used to parse the url.

        Raises:
            UnknownDomainError, if there is no registered subclass for the url domain.
        """

        for subclass in cls.registered:
            if subclass.domain.search(url):  # type: ignore
                return subclass

        raise UnknownDomainError(f"no source found for url '{url}'")

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
        if self._soup is not None:
            self._soup.decompose()

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

    def refresh(self, *, progress: Optional[Callable[[str], None]] = None):
        """Refresh the list of chapters available.

        Args:
            progress: A callback function called with the chapter id every time it is parsed.
                Defaults to None.
        """

        self.meta = self.metadata()

        for chapter in self.chapters():

            if chapter.id not in self.data:

                _log.info("manga: adding new chapter %s", chapter.id)

                self.data[chapter.id] = chapter

                if progress is not None:
                    progress(chapter.id)

    def refresh_pages(self, chapter_ids: Optional[List[str]] = None):
        """Refresh the pages available for the chapters.
        Any existing chapters with pages already are ignored.

        Args:
            chapters: A list of chapter ids to refresh.
                If None, all chapters will be refreshed (may take a while).
        """

        if chapter_ids is None:
            chapter_ids = cast(list, self.data.keys())

        for chapter_id in chapter_ids:
            chapter = self.data[chapter_id]

            if chapter.pages is None:

                _log.info("manga: adding pages to chapter %s", chapter.id)

                chapter.pages = self.pages(chapter)

    def select(self, start: str, end: str) -> List[str]:
        """Select chapter ids from the start id to the end id.
        The ids are sorted first.

        Args:
            start: The start chapter id.
            end: The end chapter id.

        Returns:
            A list of all chapter ids between start and end (inclusive of start and end).
        """

        cids = natsorted(self.data.keys())
        start_index = cids.index(start)
        end_index = cids.index(end, start_index)

        return cids[start_index : end_index + 1]

    def soup_from_url(self, url: str) -> bs4.BeautifulSoup:
        """Retreive a url and create a soup using its content."""
        return bs4.BeautifulSoup(self.session.get(url).text, BS4_PARSER)

    def download(
        self,
        cid: str,
        to: Union[str, pathlib.Path],
        *,
        progress: Optional[Callable[[int], None]] = None,
    ) -> List[pathlib.Path]:
        """Download a chapter's pages to a folder.

        Args:
            cid: The chapter id to download.
            to: The folder to download the pages to.
            progress: A callback function which is called with the page number every time a page is downloaded.
                Defaults to None.

        Returns:
            A list of absolute paths to the downloaded pages in ascending order
            (1.png, 2.png, 3.png, etc.)
        """

        to = pathlib.Path(to)

        paths = []

        chapter = self.data[cid]

        if chapter.pages is None:
            _log.warning(f"manga: [{chapter.id}] pages not found, refreshing")
            self.refresh_pages([chapter.id])

        chapter.pages = cast(list, chapter.pages)

        total = len(chapter.pages)

        with cfutures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(self.session.get, url): count
                for count, url in enumerate(chapter.pages)
            }

            for progress_count, future in enumerate(cfutures.as_completed(futures)):
                count = futures[future]

                _log.info(f"manga: [{chapter.id}] downloading page {count} of {total}")

                resp = future.result()
                path = utils.save_response(to / str(count), resp)
                paths.append(path)

                if progress is not None:
                    progress(progress_count)

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

        cls.domain = re.compile(cls.domain)
        cls.registered.append(cls)

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
        return self.index[url]["metadata"]["_hash"]

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

        self.index[manga.url] = manga.export_dict()

        manga_path = self._hash_path(manga.url)
        manga_path.mkdir(exist_ok=True)

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

        return Manga.import_dict(self.index[url])

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
