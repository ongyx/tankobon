# coding: utf8

import abc
import concurrent.futures as cfutures
import logging
import pathlib
import shutil
import typing as tp

import bs4  # type: ignore
import fake_useragent  # type: ignore

try:
    import fpdf  # type: ignore
    import imagesize  # type: ignore
    import natsort  # type: ignore
except ImportError:
    fpdf = None
    imagesize = None
    natsort = None

from tankobon import utils

# type hints
MangaData = tp.Dict[str, tp.Any]

# constants
BS4_PARSER = "html.parser"
VOLUME_NOTSET = "unknown"

_log = logging.getLogger("tankobon")

_parsers = {}
_useragent = fake_useragent.UserAgent()


class Parser(abc.ABC):
    """A manga website parser.

    Args:
        data: The manga metadata as a dict.
            These keys are required:

            'url' (str): The manga website's url.
        timeout: How long to wait for the website server to respond.
            Defaults to utils.TIMEOUT (5).

    Attributes:
        data: The manga metadata.
        domain: The website domain this parser is intended to parse.
            (i.e google.com)
        DEFAULTS: Default values for the manga metadata.
            On init, the 'data' arg is used to update these defaults into .data.
        session: The requests.Session used to retrieve urls.
        soup: The BeautifulSoup of the manga website.

    Raises:
        ValueError, if the url is invalid.
    """

    domain: tp.Optional[str] = None
    DEFAULTS: tp.Dict[str, tp.Any] = {
        "chapters": {},
        "title": None,
        "url": None,
    }

    def __init__(
        self, data: tp.Optional[MangaData] = None, timeout: int = utils.TIMEOUT
    ) -> None:
        if data is None:
            data = {}

        self.data = self.DEFAULTS
        self.data.update(data)

        url = self.data["url"]

        if not utils.is_url(url):
            raise ValueError(f"invalid url: {url}")

        self.session = utils.TimedSession()
        self.session.headers.update({"Referer": url, "User-Agent": _useragent.random})

        self.soup = self.soup_from_url(url)

    # implicitly register class
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.domain is None:
            raise TypeError("'domain' attribute needs to be overriden in subclass")

        _parsers[cls.domain] = cls

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    def close(self) -> None:
        self.session.close()
        self.soup.decompose()

    @abc.abstractmethod
    def chapters(self) -> tp.Generator[tp.Dict[str, str], None, None]:
        """Parse chapters from the webpage.

        Yields:
            A dict in the form:
            (all values must be strings)
            {
                "id": ...,  # chapter 'number'
                "title": ...,
                "url": ...,
                "volume": ...,  # volume 'number'
            }
            where volume is optional and may be undefined.
        """
        pass

    @abc.abstractmethod
    def pages(self, soup: bs4.Tag) -> tp.List[str]:
        """Parse pages from the chapter webpage.

        Args:
            soup: The soup of the url from the chapter data yielded by .chapters().

        Returns:
            A list of direct URLs to the page images in order of page number.
        """
        pass

    def title(self) -> str:
        """Parse the manga title from the webpage.

        Returns:
            The manga title.
        """
        return (
            self.soup.title.text
            or self.soup.find("meta", property="og:title")["content"]
        )

    def description(self) -> str:
        """Parse the manga description.

        Returns:
            The description.
        """
        return ""

    def soup_from_url(self, url: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(self.session.get(url).content, BS4_PARSER)

    def refresh(self) -> None:
        """Add any new chapters to the metadata."""

        self.data["title"] = self.title()
        self.data["description"] = self.description()

        _log.info("[refresh] adding new chapters")

        for chapter_data in self.chapters():
            chapter_id = chapter_data.pop("id")

            _log.debug("[refresh] adding chapter %s", chapter_id)

            if chapter_id in self.data["chapters"]:
                continue

            if "volume" not in chapter_data:
                _log.warning("[refresh] chapter %s has no volume", chapter_id)
                chapter_data["volume"] = VOLUME_NOTSET

            self.data["chapters"][chapter_id] = chapter_data

    def parse(
        self, force: bool = False, refresh: bool = True, volume: tp.Optional[str] = None
    ) -> None:
        """Parse pages from all the chapters.

        Args:
            force: Whether or not to parse chapters previously parsed.
                Defaults to False.
            refresh: Whether or not to refresh metadata for any new chapters before parsing.
                Defaults to True.
            volume: Parse chapters belonging only to a specific volume.
                If None, all chapters are parsed.
                Defaults to None.
        """

        pool = cfutures.ThreadPoolExecutor()
        results = {}

        if refresh:
            self.refresh()

        for chapter_id, chapter_data in self.data["chapters"].items():

            if chapter_data.get("pages") is not None and not force:
                _log.info("[parse] chapter %s already parsed, skipping", chapter_id)
                continue

            if volume is not None and chapter_data["volume"] != volume:
                _log.info(
                    "[parse] chapter %s not in volume %s, skipping", chapter_id, volume
                )
                continue

            # add task to pool
            _log.info("[parse] submitting task for chapter %s", chapter_id)
            future = pool.submit(self.pages, self.soup_from_url(chapter_data["url"]))
            results[future] = chapter_id

        for future in cfutures.as_completed(results):
            chapter_id = results[future]
            pages = future.result()

            _log.info(
                "[parse] adding %s pages to chapter %s", str(len(pages)), chapter_id
            )
            self.data["chapters"][chapter_id]["pages"] = pages

        _log.info("[parse] done")
        pool.shutdown()


class Downloader:
    def __init__(self, data: MangaData) -> None:
        self.data = data
        self.session = utils.TimedSession()

        self.session.headers.update({"Referer": self.data["url"]})

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    def close(self) -> None:
        self.session.close()

    def download(
        self,
        path: tp.Union[str, pathlib.Path],
        chapters: tp.Optional[tp.List[str]] = None,
        force: bool = False,
        cooldown: int = utils.COOLDOWN,
    ) -> None:
        """Download the manga to disk.
        Each chapter will be downloaded to its own folder (1, 2, 3, etc).

        Args:
            path: Where to download the manga.
            chapters: The chapters to download.
                Defaults to all chapters.
            force: Whether or not to download chapters previously downloaded.
                Defaults to False.
            cooldown: How long to wait between downloading each page.
                Defaults to utils.COOLDOWN.

        Returns:
            A dict map of chapter_id to a list of page filenames (i.e 1.png, 2.png, etc.)
        """

        path = pathlib.Path(path)
        chapters = chapters or list(self.data["chapters"])

        with cfutures.ThreadPoolExecutor() as pool:
            results = {}
            for chapter in chapters:
                chapter_path = path / chapter

                if chapter_path.is_dir():
                    _log.info("[download] chapter %s exists, skipping", chapter)
                    continue

                print(chapter)
                for page_number, page in enumerate(
                    self.data["chapters"][chapter]["pages"]
                ):
                    future = pool.submit(self.session.get, page)

                    # three-tuple of chapter number, page number, and page path
                    results[future] = (
                        chapter,
                        page_number,
                        chapter_path / str(page_number),
                    )

            for future in cfutures.as_completed(results):
                chapter, page, page_path = results[future]

                try:
                    resp = future.result()

                except Exception as e:
                    _log.critical(
                        "[download] could not download page %s for chapter %s: %s",
                        page,
                        chapter,
                        e,
                    )

                    shutil.rmtree(str(page_path.parent))
                    raise e

                else:
                    _log.info("[download] saving page %s of chapter %s", page, chapter)

                    page_path.parent.mkdir(exist_ok=True)
                    utils.save_response(page_path, resp)

    def export_pdf(self, volume: str, to: tp.Union[str, pathlib.Path]) -> None:
        """Export the manga to a PDF.
        The pages will be downloaded to the same folder as the PDF.

        Args:
            volume: Which volume to export as a PDF.
            to: Where to output the PDF.
        """

        if any(m is None for m in (fpdf, imagesize, natsort)):
            raise RuntimeError(
                "PDF extension is required for export, install with 'pip install tankobon[pdf]'"
            )

        path = pathlib.Path(to)
        chapters = [
            c for c, v in self.data["chapters"].items() if v["volume"] == volume
        ]

        self.download(path.parent, chapters=chapters)

        _log.info("[pdf] creating pdf for volume %s", volume)
        pdf = fpdf.FPDF()

        for chapter in natsort.natsorted(chapters):
            _log.info("[pdf] adding chapter %s", chapter)

            chapter_path = path / chapter

            for page in natsort.natsorted((str(p) for p in chapter_path.glob("*.*"))):
                _log.debug("[pdf] adding page %s", page)
                pdf.add_page()

                width, height = imagesize.get(page)
                page_width = 210
                page_height = 297
                ratio = min(page_width / width, page_height / height)

                # use ratio to scale correctly
                try:
                    pdf.image(page, 0, 0, w=width * ratio, h=height * ratio)
                except RuntimeError as e:
                    raise RuntimeError(page, e)

        _log.info("[pdf] saving %s.pdf", volume)
        pdf.output(str(path / f"{volume}.pdf"), "F")
