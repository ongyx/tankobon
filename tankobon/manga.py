# coding: utf8

import abc
import concurrent.futures as cfutures
import functools
from typing import Any, Dict, Generator, List, Optional

import bs4  # type: ignore
import requests

BS4_PARSER = "html.parser"
TIMEOUT = 5


class Parser(abc.ABC):
    """A manga website parser."""

    _DEFAULTS: Dict[str, Any] = {
        "chapters": {},
        "title": "",
        "url": "",
    }

    def __init__(
        self, data: Optional[Dict[str, Any]] = None, timeout: int = TIMEOUT
    ) -> None:
        if data is None:
            data = {}

        self.data = self._DEFAULTS
        self.data.update(data)

        if self.data["url"] is None:
            raise ValueError("no webpage url in database")

        self.session = requests.Session()
        self.session.headers.update({"referer": self.data["url"]})

        self.session.get = functools.partial(self.session.get, timeout=timeout)  # type: ignore[assignment]

        self.soup = self.soup_from_url(self.data["url"])

    @abc.abstractmethod
    def chapters(self) -> Generator[Dict[str, str], None, None]:
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
    def pages(self, chapter_data: Dict[str, str]) -> List[str]:
        """Parse pages from the chapter webpage.

        Args:
            chapter_data: The chapter data yielded by .chapters().

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

    def soup_from_url(self, url: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(self.session.get(url).text, BS4_PARSER)

    def parse(self, force: bool = False) -> None:
        """Parse pages from all the chapters."""

        self.data["title"] = self.title()

        for chapter in self.chapters():
            chapter_id = chapter.pop("id")

            if chapter_id in self.data["chapters"] and not force:
                continue

            self.data["chapters"][chapter_id] = chapter

        with cfutures.ThreadPoolExecutor() as pool:
            results = {
                pool.submit(self.pages, chapter["url"]): chapter_id
                for chapter_id, chapter in self.data["chapters"].items()
            }

            for future in cfutures.as_completed(results):
                chapter_id = results[future]
                self.data["chapters"][chapter_id]["pages"] = future.result()
