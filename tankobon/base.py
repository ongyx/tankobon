# coding: utf8
"""tankobon (漫画): Manga downloader and scraper."""

import abc
import json
import logging
import multiprocessing as mproc
import pathlib
from collections.abc import MutableMapping
from multiprocessing.pool import ThreadPool
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

import bs4
import requests

from . import utils
from .exceptions import CacheError

Chapter = Tuple[str, str, str]

_log = logging.getLogger("tankobon")


class Cache(MutableMapping):
    """A cache/downloader for Manga pages, stored on disk.

    Args:
        path: The path to store the cache at.
        database: The existing manga database.
            If not specified, the database will be loaded from 'index.json' in path.
    """

    CACHE_FILENAME = "index.json"

    def __init__(
        self, path: Union[str, pathlib.Path], database: Optional[dict] = None
    ) -> None:
        self.path = pathlib.Path(path)
        self.cachepath = self.path / self.CACHE_FILENAME

        # create path if it does not exist
        self.path.mkdir(exist_ok=True)

        if database is None:
            self.reload_cache()
        else:
            self.database = database

    def __getitem__(self, key):
        return self.database[key]

    def __setitem__(self, key, value):
        self.database[key] = value

    def __delitem__(self, key):
        del self.database[key]

    def __iter__(self):
        return iter(self.database)

    def __len__(self):
        return len(self.database)

    def __repr__(self):
        return f"{type(self).__name__}({self.database})"

    def reload_cache(self) -> None:
        """Load the existing cache database from self.path into self.database.

        Raises:
            CacheError, if the database does not exist.
        """

        try:
            cache = self.path / self.CACHE_FILENAME
            with cache.open() as f:
                self.database = json.load(f)
            _log.debug("reloaded cache")

        except FileNotFoundError:
            raise CacheError(f"cache at path {str(cache)} does not exist")

    def download_chapters(
        self,
        ids: Optional[List[str]] = None,
        force: bool = False,
        threads: int = utils.THREADS,
    ) -> None:
        """Download chapters, caching its pages on disk.
        Ignores any existing chapter data on disk (downloads anyway).

        Args:
            ids: The page ids. Defaults to all chapters.
            force: Whether or not to re-download chapters, regardless if they are
                already downloaded. Defaults to False.
            threads: The number of threads to use to download the pages.
                Defaults to utils.THREADS (8).
        """

        if ids is None:
            ids = self.database["chapters"].keys()

        for id in ids:

            chapter_path = self.path / id
            if chapter_path.exists() and not force:
                _log.info(f"skipping chapter {id}")
                continue
            _log.info(f"downloading chapter {id}")

            chapter_path.mkdir(exist_ok=True)
            urls = self.database["chapters"][id]["pages"]

            with ThreadPool(threads) as pool:
                responses = pool.imap(requests.get, urls)

                for page_number, response in enumerate(responses):
                    _log.debug("downloading page %s", page_number)

                    page_path = (
                        chapter_path
                        / f"{page_number}{utils.get_file_extension(response)}"
                    )

                    with page_path.open(mode="wb+") as f:
                        f.write(response.content)

    def close(self):
        with self.cachepath.open("w+") as f:
            json.dump(self.database, f)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if tb is None:
            self.close()


class GenericManga(abc.ABC):
    """A generic manga website.

    Args:
        database: The inital database of the manga as a dictionary.
            It must be in this format:
            {
                "title": "...",  # manga title/name
                "url": "...",  # manga index (chapter listing)
                "chapters": {...}  # cached chapter info, automatically generated
            }
            where 'title' and 'url' must be specified, and 'chapters' may be an empty
            dict.
        update: Whether or not to download and parse the index, adding any new
            chapters. Defaults to True.

    Attributes:
        database (dict): see args
        soup (bs4.BeautifulSoup): The soup of the HTML.
    """

    # you should overrride this
    DEFAULTS: Dict[str, Any] = {}

    def __init__(
        self,
        database: Optional[Union[dict, Cache]] = None,
        update: bool = True,
    ) -> None:
        if database is None:
            self.database = self.DEFAULTS
        else:
            self.database = database  # type: ignore

        self.soup = utils.get_soup(self.database["url"])
        if update:
            self.refresh()

    def __getattr__(self, key):
        value = self.database.get(key)
        if value is None:
            raise AttributeError
        return value

    def query(self, query: str) -> Any:
        """A much nicer way to get values from a dictionary.

        Args:
            query: The query, in the format 'key1:keyX' where ':' seperates
                successive keys and is evaluated to ['key1']['keyX'].
                Keys must not have ':' in their names.
        """

        value = None

        if not self.database:
            raise ValueError("database is empty")

        for key in query.split(":"):
            value = value or self.database
            value = value[key]
        return value

    @staticmethod
    def is_link(tag: bs4.element.Tag) -> bool:
        """Check whether a BeautifulSoup tag is a link.

        Args:
            tag: The tag.

        Returns:
            True if so, otherwise False.
        """

        return (tag.name == "a") and (tag.get("href") is not None)

    def is_parsed(self, id: str) -> bool:
        """Check whether a chapter has already been parsed to get its page URLs.

        Args:
            id: The chapter id.

        Returns:
            True if so, otherwise False.
        """

        try:
            return bool(self.database["chapters"][id]["url"])
        except KeyError:
            return False

    @abc.abstractmethod
    def parse_chapters(self) -> Generator[Chapter, None, None]:
        """Parse all chapters from the soup.

        Yields:
            A three-tuple of (chapter_id, chapter_title, chapter_url).
        """

        raise NotImplementedError

    @abc.abstractmethod
    def parse_pages(self, id: str, force: bool = False) -> list:
        """Parse all pages from a chapter.
        The chapter's info must have already been cached into the database.

        The chapter webpage's HTML should be downloaded and parsed for page links.
        The page URLs will be cached in the database and returned if requested
        subsequently (won't parse again).

        Args:
            id: The chapter id.
            force: Whether or not to re-parse the chapter webpage for pages,
                regardless of whether or not the pages have already been parsed.
                Defaults to False.

        Returns:
            A list of page URLs.
        """

        raise NotImplementedError

    def refresh(self, force: bool = False) -> None:
        """Refresh the database, adding any new chapter info.
        Does not download the chapter webpages (under the 'pages' key).

        Args:
            force: Whether or not to overwrite any existing chapters with newer data.
        """

        for id, title, url in self.parse_chapters():
            if self.is_parsed(id) and not force:
                continue
            self.database["chapters"][id] = {"url": url, "title": title, "pages": []}

    @property
    def existing_chapters(self) -> Generator[Chapter, None, None]:
        """Generate existing chapters cached into the database.

        Yields:
            A three-tuple of (id, title, url).
        """
        for id, chapter in self.database["chapters"].items():
            yield id, chapter["title"], chapter["url"]

    def parse_all(self, threads: int = utils.THREADS, force: bool = False) -> dict:
        """Parse all chapters, adding their page URLs to their info.

        Args:
            threads: How many threads to use to speed up parsing.
                Defaults to THREADS (8).
            force: Whether or not to parse all chapters, regardless of whether or not
                the chapter's pages have already been parsed. Defaults to False.

        Returns:
            The info of all chapters mapped to their ids.
        """

        def _parse_all(args):
            id, title, url = args
            if self.database["chapters"][id]["pages"] and not force:
                _log.info(f"skipping {id}")
                return
            pages = self.parse_pages(id, force=True)
            _log.info(f"parsed {id}")
            return id, {"title": title, "url": url, "pages": pages}

        with ThreadPool(threads) as pool:
            results = pool.imap_unordered(_parse_all, self.existing_chapters)

            for result in results:
                if result is None:
                    continue
                id, chapter = result
                self.database[id] = chapter

        return self.database
