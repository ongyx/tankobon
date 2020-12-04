# coding: utf8

import re

from tankobon.base import GenericManga


class Manga(GenericManga):

    RE_TITLE = re.compile(r"(.*) Manga *\|")
    RE_CHAPTER = re.compile(r"Chapter (\d+)\:? ?([\w \(\)]*)")

    def get_title(self):
        return self.RE_TITLE.findall(super().get_title())[0]

    def get_pages(self, url):
        soup = self.get_soup(url)

        pages = []
        pages_div = soup.find("div", class_="container-chapter-reader")
        if not pages_div:
            return

        for link in pages_div.find_all("img", src=True):
            pages.append(link["src"])

        return pages

    def get_chapters(self):
        for tag in self.soup.find_all("a", class_="chapter-name"):
            href = str(tag.get("href"))
            title = str(tag.text)

            match = self.RE_CHAPTER.findall(title)

            if match:
                id, title = match[0]
                yield id, {"title": title, "url": href}
