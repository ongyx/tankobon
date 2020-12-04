# coding: utf8

import re

from tankobon.base import GenericManga


class Manga(GenericManga):
    RE_CHAPTER = re.compile(r".*[Cc]hapter ?([\d\.]+) ?:? ?(.*)")

    def get_title(self):
        return self.soup.find("ul", class_="manga-info-text").li.h1.text

    def get_pages(self, url):
        soup = self.get_soup(url)

        return [
            tag["src"]
            for tag in soup.find("div", class_="vung-doc").find_all("img", src=True)
        ]

    def get_chapters(self):
        for tag in self.soup.find_all("div", class_="row"):
            link = tag.span.a
            if not link:
                continue

            chapter, title = self.RE_CHAPTER.findall(link.text)[0]
            yield chapter, {"title": title, "url": link["href"]}
