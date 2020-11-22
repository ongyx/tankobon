# coding: utf8
"""Bootstrap for Komi Can't Communicate."""

import re

from tankobon.base import GenericManga

_RE_OMAKE = re.compile(r"\.\d")


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

    def cover(self):
        return self.soup.find("img", class_="wp-image-1419", srcset=True)[
            "srcset"
        ].split()[0]

    def parse_volumes(self):
        chapters = self.sorted()
        volumes = {}
        omake = []
        for index, chapter in enumerate(chapters):
            if _RE_OMAKE.match(chapter):
                omake.append(index)

        for volume, end in enumerate(omake):
            if end == 0:
                start = 0
            else:
                start = omake[end - 1]

            volumes[volume] = chapters[start:end]

        return volumes

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

        for tag in self.soup.find_all("a", href=True):

            href = str(tag.get("href"))
            title = str(tag.text)

            match = self.RE_TITLE.findall(title)

            if match:
                id, title = match[0]
                yield id, title, href
