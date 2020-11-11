# coding: utf8
"""Bootstrap for Komi Can't Communicate."""

import re

from tankobon.base import GenericManga


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

    def parse_pages(self, soup):
        pages = []
        # pages_div = soup.find("div", class_="post-body entry-content")
        # if not pages_div:
        #    return

        for link in soup.find_all("img", src=True):
            if "blogspot.com" in link["src"]:
                pages.append(link["src"])

        return pages

    def parse_chapters(self):
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
