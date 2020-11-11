# coding: utf8
"""tankobon (漫画): Manga downloader and scraper."""

import abc
import logging
import functools
import pathlib
from multiprocessing.pool import ThreadPool as Pool
from typing import Any, Dict, Generator, List, Optional, Tuple

import bs4
import requests
import requests_random_user_agent  # noqa: F401

from . import utils

Chapters = Generator[Tuple[str, str, str], None, None]

_log = logging.getLogger("tankobon")


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
            where 'title' and 'url' must be specified,
            and 'chapters' may be an empty dict.
        update: Whether or not to download and parse the index, adding any new
            chapters. Defaults to True.

    Attributes:
        database (dict): see args
        soup (bs4.BeautifulSoup): The soup of the HTML.
    """

    # you should overrride this
    DEFAULTS: Dict[str, Any] = {}

    def __init__(
        self, database: Optional[dict] = None, update: bool = True, force: bool = False
    ) -> None:
        self.database = self.DEFAULTS
        self.database.update(database)  # type: ignore
        self._force = force

        if "chapters" not in self.database:
            self.database["chapters"] = {}

        self.soup = utils.get_soup(self.database["url"])
        if update:
            self.refresh()

    def __getattr__(self, key):
        value = self.database.get(key)
        if value is None:
            raise AttributeError
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
            return bool(self.database["chapters"][id]["pages"])
        except KeyError:
            return False

    @abc.abstractmethod
    def parse_chapters(self) -> Chapters:
        """Parse all chapters from the soup.

        Yields:
            A three-tuple of (chapter_id, chapter_title, chapter_url).
        """

        raise NotImplementedError

    @abc.abstractmethod
    def parse_pages(self, soup: bs4.BeautifulSoup) -> List[str]:
        """Parse all pages from a chapter.
        The chapter's info must have already been cached into the database.

        Args:
            soup: The soup of the chapter's url.

        Returns:
            A list of the chapter's pages.
        """
        raise NotImplementedError

    def refresh(self) -> None:
        """Refresh the database, adding any new chapter info.
        Does not download the chapter webpages (under the 'pages' key).

        Args:
            force: Whether or not to overwrite any existing chapters with newer data.
        """

        for id, title, url in self.parse_chapters():
            if self.is_parsed(id) and not self._force:
                continue
            self.database["chapters"][id] = {"url": url, "title": title, "pages": []}

    @property
    def existing_chapters(self) -> Chapters:
        """Generate existing chapters cached into the database.

        Yields:
            A three-tuple of (id, title, url).
        """
        for id, chapter in self.database["chapters"].items():
            yield id, chapter["title"], chapter["url"]

    def _parse_all(self, args):
        id, title, url = args
        if self.is_parsed(id) and not self._force:
            _log.info(f"skipping {id}")
            return
        pages = self.parse_pages(utils.get_soup(url, encoding="utf-8"))
        _log.info(f"parsed {id}")
        return id, {"title": title, "url": url, "pages": pages}

    def parse_all(self, threads: int = utils.THREADS) -> dict:
        """Parse all chapters, adding their page URLs to their info.

        Args:
            threads: How many threads to use to speed up parsing.
                Defaults to THREADS (8).

        Returns:
            The info of all chapters mapped to their ids.
        """

        with Pool(threads) as pool:
            results = pool.imap_unordered(
                self._parse_all, self.existing_chapters  # type: ignore
            )

            for result in results:
                if result is None:
                    continue
                id, chapter = result
                self.database["chapters"][id] = chapter

        return self.database

    def download_chapters(
        self,
        path: pathlib.Path,
        ids: Optional[List[str]] = None,
        force: bool = False,
        threads: int = utils.THREADS,
    ) -> None:
        """Download chapters, caching its pages on disk.
        Ignores any existing chapter data on disk (downloads anyway).

        Args:
            path: Where to download the chapters to.
            ids: The page ids. Defaults to all chapters.
            force: Whether or not to re-download chapters, regardless if they are
                already downloaded. Defaults to False.
            threads: The number of threads to use to download the pages.
                Defaults to utils.THREADS (8).
        """

        if ids is None:
            ids = self.database["chapters"].keys()

        for id in ids:

            chapter_path = path / id
            if chapter_path.exists() and not force:
                _log.info(f"skipping chapter {id}")
                continue
            _log.info(f"downloading chapter {id}")

            chapter_path.mkdir(exist_ok=True)
            urls = self.database["chapters"][id]["pages"]

            with Pool(threads) as pool:
                session = requests.Session()
                # hehe boi
                session.headers.update(
                    {"referer": self.database["chapters"][id]["url"]}
                )
                responses = pool.imap(session.get, urls)

                for page_number, response in enumerate(responses):
                    _log.debug("downloading page %s", page_number)

                    page_path = (
                        chapter_path
                        / f"{page_number}{utils.get_file_extension(response)}"
                    )

                    with page_path.open(mode="wb+") as f:
                        f.write(response.content)
