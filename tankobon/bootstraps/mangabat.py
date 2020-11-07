# coding: utf8

import re

from tankobon.base import GenericManga, Chapters


class Manga(GenericManga):

    RE_TITLE = re.compile(r"(.*) Manga *\|")
    RE_CHAPTER = re.compile(r"Chapter (\d+) ?(.*)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database["title"] = RE_TITLE.findall(
            soup.find("meta", property="og:title").content
        )[0]

    def page_is_valid(self, tag):
        return "M.MangaBat.com" in tag.title

    def parse_chapters(self) -> Chapters:
        for tag in self.soup.find_all("a", class_="chapter-name"):
            href = tag.get("href")
            title = tag.text

            match = self.RE_CHAPTER.findall(title)

            if match:
                id, title = match[0]
                yield id, title, href