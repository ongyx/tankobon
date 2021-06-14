# coding: utf8
"""Core functionality of tankobon."""

from __future__ import annotations

import abc
import concurrent.futures as cfutures
import gzip
import logging
import pathlib
import re
import shutil
from typing import cast, Callable, Dict, List, Optional, Type, Union

import bs4  # type: ignore
import fpdf  # type: ignore
import imagesize  # type: ignore
import natsort  # type: ignore
import requests.exceptions

from . import models, utils
from .exceptions import MangaNotFoundError, PagesNotFoundError, UnknownDomainError

_log = logging.getLogger("tankobon")

A4_WIDTH = 210
A4_HEIGHT = 297

SHORT_HASH_LEN = 8


class Parser(abc.ABC):

    # This allows subclasses to be registered.
    registered: List[Type[Parser]] = []

    def __init__(self):
        self.session = utils.UserSession()

    def create(self, url: str) -> models.Manga:
        """Create a new manga.

        Args:
            url: The manga url.

        Returns:
            A Manga object.
        """

        metadata = self.metadata(url)
        return models.Manga(metadata)

    @classmethod
    def parser(cls, url: str) -> Parser:
        """Get the appropiate parser subclass for the domain in url.

        Args:
            url: The url to get the subclass for.

        Returns:
            The subclass instance that can be used to parse the url.

        Raises:
            UnknownDomainError, if there is no registered subclass for the url domain.
        """

        for subclass in cls.registered:
            if subclass.domain.search(url):  # type: ignore
                return subclass()

        raise UnknownDomainError(f"no source found for url '{url}'")

    @property
    @abc.abstractmethod
    def domain(self) -> str:
        pass

    @abc.abstractmethod
    def metadata(self, url: str) -> models.Metadata:
        """Parse metadata for a manga url.

        Args:
            url: The manga url.

        Returns:
            The Metadata object.
        """

    @abc.abstractmethod
    def add_chapters(self, manga: models.Manga):
        """Add chapters to the manga.

        This method should add every chapter in the manga as a Chapter object:

        ```python
        def chapters(self, manga):
            for ... in ...:
                # do your parsing here
                manga.add(Chapter(...))
        ```

        Only the 'url' and 'id' args are required when creating a Chapter.
        The other fields are optional and have default values (see `help(tankobon.models.Chapter)`).

        Args:
            manga: The manga object.
        """

    @abc.abstractmethod
    def add_pages(self, chapter: models.Chapter):
        """Add pages to the chapter in the manga as a list of urls.
        The pages must be in ascending order.

        This method should assign pages to the chapter:

        ```python
        def pages(self, chapter):
            # do your parsing here
            chapter.pages = [...]  # assign directly to the chapter's pages.
        ```

        Args:
            chapter: The chapter object (already added to the manga).
        """

    def soup(self, url: str) -> bs4.BeautifulSoup:
        """Get a soup from a url.

        Args:
            url: The url to get a soup from.

        Returns:
            The soup of the url.
        """

        return utils.soup(url, session=self.session)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.domain = re.compile(cls.domain)
        cls.registered.append(cls)


class Cache(utils.PersistentDict):
    """A manga cache.

    Args:
        root: The root of the cache.

    Attributes:
        root: See args.
        alias: A map of manga url to manga hash.
    """

    INDEX = "index.json.gz"

    def __init__(self, root: Union[str, pathlib.Path] = utils.ROOT):
        if isinstance(root, str):
            root = pathlib.Path(root)

        self.root = root

        index = self.root / self.INDEX
        old_index = self.root / "index.json"

        if old_index.is_file():
            # indexes are now compressed by default so compress the old one
            with gzip.open(index, "wt") as f:
                f.write(old_index.read_text())

            old_index.unlink()

        super().__init__(self.root / self.INDEX, compress=True)

        self.alias: Dict[str, str] = {}

        # alias urls to their hashes
        for hash, manga in self.data.items():
            self.alias[manga["meta"].url] = hash

    def fullhash(self, part: str) -> str:
        """Get the full SHA512 hash of a manga when only given at least the first 8 letters of the hash.

        Args:
            part: The first 8 letters of the hash.

        Returns:
            The full hash, or an empty string if part was not found.

        Raises:
            ValueError, if the length part is less than 8.
        """
        if len(part) < SHORT_HASH_LEN:
            raise ValueError(f"part {part} is too short")

        for hash in self.data:
            if hash.startswith(part):
                return hash

        return ""

    def dump(self, manga: models.Manga):
        """Save this manga within the cache.

        Args:
            manga: The manga object to save.
        """

        self.data[manga.meta.hash] = manga.dump()

        self.alias[manga.meta.url] = manga.meta.hash

        (self.root / manga.meta.hash).mkdir(exist_ok=True)

    def load(self, hash: str) -> models.Manga:
        """Load a manga by its hash.

        Args:
            hash: The manga hash.

        Returns:
            The Manga object.

        Raises:
            MangaNotFoundError, if the manga does not exist in the cache.
        """

        if hash not in self.data:
            raise MangaNotFoundError(f"{hash} does not exist in cache")

        return models.Manga.load(self.data[hash])

    def delete(self, hash: str):
        """Delete a manga from the cache.

        Args:
            hash: The manga hash.

        Raises:
            MangaNotFoundError, if the manga does not exist in the cache.
        """
        if hash not in self.data:
            raise MangaNotFoundError(f"{hash} does not exist in cache")

        del self.alias[self.data[hash]["meta"].url]
        shutil.rmtree(str(self.root / hash))
        del self.data[hash]


class Downloader:
    """A manga downloader.

    Args:
        path: The path to where the manga chapters will be downloaded.
            For every manga chapter, a corrosponding folder is created if it does not exist.
    """

    MANIFEST = "manifest.json"

    def __init__(self, path: Union[str, pathlib.Path]):
        if isinstance(path, str):
            path = pathlib.Path(path)

        self.path = path

        self.session = utils.UserSession()
        self.manifest = utils.PersistentDict(self.path / self.MANIFEST)

    def close(self):
        self.session.close()
        self.manifest.close()

    def download(
        self,
        chapter: models.Chapter,
        *,
        force: bool = False,
        progress: Optional[Callable[[int], None]] = None,
    ):
        """Download pages for a chapter.

        Args:
            chapter: The Chapter object to download.
            force: Whether or not to re-download the chapter if it already exists.
                Defaults to False.
            progress: A callback function which is called with the page number every time a page is downloaded.
                Defaults to None.

        Raises:
            PagesNotFoundError, if the chapter to be downloaded has no pages.
        """

        self.session.headers.update({"Referer": chapter.url})

        if not chapter.pages:
            raise PagesNotFoundError(f"chapter {chapter.id} does not have any pages")

        entry = self.manifest.setdefault(chapter.id, {})

        if chapter.lang in entry and not force:
            # bail out: dont re-download chapter
            return

        chapter.pages = cast(list, chapter.pages)

        chapter_path = self.path / chapter.id / chapter.lang
        chapter_path.mkdir(parents=True)

        pages = []
        total = len(chapter.pages)

        with cfutures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(self.session.get, url): count
                for count, url in enumerate(chapter.pages)
            }

            # progress count is different from page number as the page futures may not be in order.
            for p_count, future in enumerate(cfutures.as_completed(futures)):
                count = futures[future]

                _log.info(
                    f"downloader: [{chapter.id}] downloading page {count} of {total}"
                )

                try:
                    resp = future.result()
                    resp.raise_for_status()

                except requests.exceptions.RequestException as e:
                    _log.critical(f"downloader: failed to download page {count}: {e}")

                    # cant partially download, so remove chapter folder
                    shutil.rmtree(chapter_path)

                    raise e

                path = utils.save_response(chapter_path / str(count), resp)
                pages.append(str(path))

                if progress is not None:
                    progress(p_count)

        self.manifest[chapter.id][chapter.lang] = pages

    def download_cover(self, manga: models.Manga):
        """Download a manga's cover to the download path as 'cover.(ext)'.

        Args:
            manga: The manga to download a cover for.
        """

        self.session.headers.update({"Referer": manga.meta.url})

        with self.session.get(manga.meta.cover) as resp:
            utils.save_response(self.path / "cover", resp)

    def pdfify(
        self,
        chapters: List[str],
        dest: Union[str, pathlib.Path],
        lang: str = "en",
    ):
        """Create a PDF out of several (downloaded) chapters.
        The PDF will be A4 sized (vertical).

        Args:
            chapters: The chapters to create a PDF for.
            lang: The language of the chapters.
                Defaults to 'en'.
            dest: Where to write the PDF to.
        """

        document = fpdf.FPDF()

        for cid in natsort.natsorted(chapters):
            _log.info(f"pdf: adding chapter {cid}")

            pages = self.manifest[cid][lang]
            total = len(pages) - 1

            for page in natsort.natsorted(pages):
                _log.debug(f"adding page {page} of {total}")
                page_path = self.path / cid / lang / page

                width, height = imagesize.get(page_path)
                ratio = min(A4_WIDTH / width, A4_HEIGHT / height)

                document.add_page()
                document.image(str(page_path), 0, 0, w=width * ratio, h=height * ratio)

        document.output(str(dest), "F")

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()
