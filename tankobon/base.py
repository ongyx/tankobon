# coding: utf8
"""tankobon (漫画): Manga downloader and scraper."""

import abc
import functools
import io
import logging
import pathlib
import tempfile
import time
from multiprocessing.pool import ThreadPool as Pool
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import bs4
import fpdf
import natsort
import requests
import requests_random_user_agent  # noqa: F401

from tankobon import utils
from tankobon.exceptions import TankobonError

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
        self, database: dict = {}, update: bool = True, force: bool = False
    ) -> None:
        self.database = self.DEFAULTS
        self.database.update(database)  # type: ignore
        self._force = force

        self.database.setdefault("chapters", {})

        self.session = requests.Session()
        # hehe boi
        self.session.headers.update({"referer": self.database["url"]})

        self.soup = utils.get_soup(self.database["url"], session=self.session)
        if update:
            self.refresh()
            self.database["volumes"] = self.parse_volumes()

    def __getattr__(self, key):
        value = self.database.get(key)
        if value is None:
            raise AttributeError
        return value

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

    def sorted(self) -> List[str]:
        return natsort.natsorted(self.database["chapters"])

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

    def parse_volumes(self) -> Dict[str, List[str]]:
        """Parse chapter ids into a volume representation like so:
        {
            "0": {
                "chapters": [...],  # list of chapter ids
                "cover": ...  # the volume cover
            },
            ...  # and so on.
        }
        By default this returns the chapters split into chunks of 20.
        The "cover" key is optional. If not provided, the cover is set as
        the first page of the first chapter of the volume.

        Returns:
            A map of volume ids to a list of chapter ids.
        """
        chapters = self.sorted()
        return {
            str(v): c
            for v, c in enumerate(
                [chapters[x : x + 20] for x in range(0, len(chapters), 20)]
            )
        }

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
        pages = self.parse_pages(
            utils.get_soup(url, encoding="utf-8", session=self.session)
        )
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
        path: Union[str, pathlib.Path],
        ids: Optional[List[str]] = None,
        force: bool = False,
        threads: int = utils.THREADS,
        cooldown: int = 2,
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
            cooldown: How long to wait before downloading each page.
                Defaults to 2.
        """

        path = pathlib.Path(path) if not isinstance(path, pathlib.Path) else path
        self._image_paths: Dict[str, List[str]] = {}

        if ids is None:
            ids = self.database["chapters"].keys()

        def session_get(*args, **kwargs):
            nonlocal self
            nonlocal cooldown
            time.sleep(cooldown)
            try:
                return self.session.get(*args, **kwargs)
            except requests.exceptions.ConnectionError as e:
                raise requests.exceptions.ConnectionError(e, args, kwargs)

        for id in ids:

            self._image_paths[id] = []

            chapter_path = path / id
            if chapter_path.exists() and not force:
                _log.info(f"skipping chapter {id}")
                continue
            _log.info(f"downloading chapter {id}")

            chapter_path.mkdir(exist_ok=True)
            urls = self.database["chapters"][id]["pages"]

            with Pool(threads) as pool:
                responses = pool.imap(session_get, urls)

                for page_number, response in enumerate(responses):
                    _log.debug("downloaded page %s from %s", page_number, response.url)

                    page_path = chapter_path / f"{page_number}"
                    try:
                        utils.save_response(page_path, response)
                    except KeyError:
                        # there is no content type (text/html, problably)
                        raise TankobonError(f"page '{response.url}' is not an image")
                    self._image_paths[id] += str(page_path)

    def download_volumes(
        self,
        path: Union[str, pathlib.Path],
        volumes: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """Download volumes, by downloading the chapters first and adding their pages to a PDF.

        Args:
            path: Where to download the volumes (as {volume_number}.pdf).
            volumes: The volumes to download.
                If None, all volumes are downloaded.
            **kwargs: Passed to download_chapters.
        """
        path = pathlib.Path(path) if not isinstance(path, pathlib.Path) else path
        chapters_to_download = []

        if volumes is None:
            volumes = self.database["volumes"].keys()

        # download required chapters first
        for volume in volumes:
            chapters_to_download.extend(self.database["volumes"][volume]["chapters"])
        self.download_chapters(path, ids=chapters_to_download, **kwargs)

        for volume in volumes:
            pdf = fpdf.FPDF()
            volume_info = self.database["volumes"][volume]
            cover_url = volume_info.get("cover")
            if cover_url is not None:
                cover_path = str(
                    utils.save_response(
                        path / f"cover_{volume}",
                        self.session.get(cover_url),
                    )
                )
                pdf.add_page()
                pdf.image(cover_path)

            for chapter in volume_info["chapters"]:
                for page in self._image_paths[chapter]:
                    pdf.add_page()
                    pdf.image(page)

            pdf.output(str(path / f"{volume}.pdf"), "F")
