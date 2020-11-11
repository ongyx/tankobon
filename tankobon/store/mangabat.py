# coding: utf8

import re

from tankobon.base import GenericManga


class Manga(GenericManga):

    RE_TITLE = re.compile(r"(.*) Manga *\|")
    RE_CHAPTER = re.compile(r"Chapter (\d+) ?(.*)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database["title"] = self.RE_TITLE.findall(
            self.soup.find("meta", property="og:title")["content"]
        )[0]

    def parse_pages(self, soup):

        pages = []
        pages_div = soup.find("div", class_="container-chapter-reader")
        if not pages_div:
            return

        for link in pages_div.find_all("img", src=True):
            pages.append(link["src"])

        return pages

    def parse_chapters(self):
        for tag in self.soup.find_all("a", class_="chapter-name"):
            href = tag.get("href")
            title = tag.text

            match = self.RE_CHAPTER.findall(title)

            if match:
                id, title = match[0]
                yield id, title, href
