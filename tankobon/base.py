# coding: utf8
"""tankobon (漫画): Manga downloader and scraper."""

import abc
import functools
import io
import logging
import pathlib
import shutil
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

    def __init__(self, database: dict = {}, update: bool = False) -> None:
        self.database = self.DEFAULTS
        self.database.update(database)  # type: ignore

        self.database.setdefault("chapters", {})

        self.session = requests.Session()
        # hehe boi
        self.session.headers.update({"referer": self.database["url"]})

        self.soup = utils.get_soup(self.database["url"], session=self.session)
        if update:
            self.refresh()
            self.database["covers"] = self.get_covers()

    def __getattr__(self, key):
        value = self.database.get(key)
        if value is None:
            raise AttributeError
        return value

    def sorted(self) -> List[str]:
        return natsort.natsorted(self.database["chapters"])

    def refresh(self) -> None:
        """Add all (new) chapters to the database."""
        for chapter, chapter_info in self.get_chapters():
            if chapter in self.database["chapters"]:
                continue
            self.database["chapters"][chapter] = chapter_info

    def get_soup(self, url: str) -> bs4.BeautifulSoup:
        """Get a soup from a url.

        Args:
            url: The url.

        Returns:
            The soup object.
        """
        return utils.get_soup(url, session=self.session)

    @abc.abstractmethod
    def get_chapters(self) -> Generator[Tuple[str, Dict[str, str]], None, None]:
        """Get all chapters in the manga.
        You must override this.

        Yields:
            A two-tuple of (chapter, chapter_info)
            where chapter is the chapter number and chapter_info is a dict:
            {
                "title": "chapter title",
                "url": "chapter url",
                "volume": "volume, i.e '0'",
            }
        """

    @abc.abstractmethod
    def get_pages(self, chapter_url: str) -> List[str]:
        """Get all pages for a chapter, given its url.
        You must override this.

        Args:
            chapter_url: The url of the chapter.
        Returns:
            A list of urls of the pages.
        """

    @abc.abstractmethod
    def get_covers(self) -> Dict[str, str]:
        """Get all covers for the manga volumes.
        Overriding this is optional, the cover won't be downloaded if it does not exist.

        Returns:
            A dictionary where volume numbers are mapped to the url of the cover:
            {
                "0": "...",
                ...
            }
        """
        return {}

    def _parse(self, args):
        chapter, chapter_info = args
        if chapter_info.get("pages"):
            _log.info(f"[parse] skipping {chapter}")
            return None, None
        _log.info(f"[parse] parsing {chapter}")
        return chapter, self.get_pages(chapter_info["url"])

    def parse(
        self, chapters: Optional[List[str]] = None, threads: int = utils.THREADS
    ) -> List[str]:
        """Parse chapters, adding their pages to the database.

        Args:
            chapters: The chapters to parse. If None, all chapters are parsed.
                Defaults to None.
            threads: How many threads to use to speed up parsing.
                Defaults to THREADS (8).

        Returns:
            The chapters that were parsed.
        """
        if chapters is None:
            chapters = self.database["chapters"].keys()

        with Pool(threads) as pool:
            results = pool.imap_unordered(
                self._parse, [(c, self.database["chapters"][c]) for c in chapters]
            )

            for chapter, pages in results:
                if not chapter or not pages:
                    continue
                self.database["chapters"][chapter]["pages"] = pages

        return chapters

    def download_chapters(
        self,
        path: Union[str, pathlib.Path],
        chapters: Optional[List[str]] = None,
        force: bool = False,
        threads: int = utils.THREADS,
        cooldown: int = 2,
    ) -> None:
        """Download chapters, caching its pages on disk.

        Args:
            path: Where to download the chapters to.
            chapters: The chapters to download. Defaults to all chapters.
            force: Whether or not to re-download chapters, regardless if they are
                already downloaded. Defaults to False.
            threads: The number of threads to use to download the pages.
                Defaults to utils.THREADS (8).
            cooldown: How long to wait before downloading each page.
                Defaults to 2.
        """

        path = pathlib.Path(path) if not isinstance(path, pathlib.Path) else path

        chapters = self.parse(chapters=chapters)

        def session_get(*args, **kwargs):
            nonlocal self
            nonlocal cooldown
            time.sleep(cooldown)
            try:
                return self.session.get(*args, **kwargs)
            except requests.exceptions.ConnectionError as e:
                _log.error("%s: @s", e, str(args))

        for chapter in chapters:

            chapter_path = path / chapter
            if chapter_path.exists() and not force:
                _log.info(f"[download] skipping chapter {chapter}")
                continue
            _log.info(f"[download] downloading chapter {chapter}")

            try:
                chapter_path.mkdir(exist_ok=True)
                urls = self.database["chapters"][chapter]["pages"]

                with Pool(threads) as pool:
                    responses = pool.imap(session_get, urls)

                    for page_number, response in enumerate(responses):
                        _log.debug(
                            "[download] downloaded page %s from %s",
                            page_number,
                            response.url,
                        )

                        page_path = chapter_path / f"{page_number}"
                        try:
                            utils.save_response(page_path, response)
                        except KeyError:
                            # there is no content type (text/html, problably)
                            raise TankobonError(
                                f"page '{response.url}' is not an image"
                            )
            except:
                _log.critical(
                    "[download] could not download all pages for chapter %s, removing chapter dir",
                    chapter,
                )
                shutil.rmtree(str(chapter_path))
                raise

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
        chapters_to_download: List[str] = []

        # we use sets for faster lookup
        if volumes is None:
            _volumes = {c["volume"] for c in self.database["chapters"].values()}
        else:
            _volumes = set(volumes)  # type: ignore
        volume_map: Dict[str, List[str]] = {v: [] for v in _volumes}

        for chapter, chapter_info in self.database["chapters"].items():
            volume = chapter_info["volume"]
            if volume in volume_map:
                volume_map[volume].append(chapter)

        for volume, chapters in volume_map.items():
            # download required chapters first
            self.download_chapters(path, chapters=chapters, **kwargs)
            _log.info("[pdf] creating pdf for volume %s", volume)
            pdf = fpdf.FPDF()
            cover_url = self.database["covers"].get(volume)
            if cover_url is not None:
                _log.debug("[pdf] adding cover from %s", cover_url)
                cover_path = str(
                    utils.save_response(
                        path / f"cover_{volume}",
                        self.session.get(cover_url),
                    )
                )
                pdf.add_page()
                pdf.image(cover_path)

            for chapter in natsort.natsorted(chapters):
                _log.info("[pdf] adding chapter %s", chapter)
                chapter_path = path / chapter
                for page in natsort.natsorted(
                    (str(p) for p in chapter_path.glob("*.*"))
                ):
                    _log.debug("[pdf] adding page %s", page)
                    pdf.add_page()
                    try:
                        pdf.image(page, 0, 0, 210, 297)
                    except RuntimeError as e:
                        raise RuntimeError(page, e)

            _log.info("[pdf] saving %s.pdf", volume)
            pdf.output(str(path / f"{volume}.pdf"), "F")
