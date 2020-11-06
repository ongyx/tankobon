# coding: utf8
"""Bootstrap for Komi Can't Communicate."""

import json
import pathlib
import re
from typing import Generator

from tankobon.base import GenericManga, Chapter
from tankobon.utils import get_soup


class Manga(GenericManga):

    IMGHOST = "blogspot.com"
    RE_TITLE = re.compile(r"(?:.*)Chapter (\d+(?:\.\d)?) *[:\-] *(.+)\Z")
    # not used, kept here for reference
    RE_URL = re.compile(r"(?:.*)?chapter-(\d+(?:-\d)?)-([\w\-]*)/?\Z")

    DEFAULTS = {
        "title": "Komi Can't Communicate",
        "url": "https://komi-san.com",
        "chapters": {},
    }

    def page_is_valid(self, url: str) -> bool:
        """Check if a page url is valid.

        Returns:
            True if so, otherwise False.
        """

        return self.IMGHOST in url

    def parse_chapters(self) -> Generator[Chapter, None, None]:
        """Generate all chapters in the manga.

        Yields:
            A three-tuple of (id, title, url) for each chapter.
        """

        # get rid of section
        section = self.soup.find("section", class_="widget ceo_latest_comics_widget")
        if section is not None:
            section.decompose()

        for tag in self.soup.find_all("a"):

            if not self.is_link(tag):
                continue
            href = tag.get("href")
            title = tag.text

            match = self.RE_TITLE.findall(title)

            if match:
                id, title = match[0]
                yield id, title, href

    def parse_pages(self, id: str, force: bool = False) -> list:
        pages = []
        soup = get_soup(self.database["chapters"][id]["url"], encoding="utf-8")

        if not (self.is_parsed(id) and not force):

            for link in soup.find_all("img"):
                src = link["src"]
                if self.page_is_valid(src):
                    pages.append(src)

            self.database["chapters"][id]["pages"] = pages

        return self.database["chapters"][id]["pages"]