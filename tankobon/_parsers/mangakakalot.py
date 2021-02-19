# coding: utf8

import re

from tankobon import manga


RE_CHAPTER = re.compile(r".*[Cc]hapter ?([\d\.]+) ?:? ?(.*)")


class Parser(manga.Parser):

    domain = "mangakakalot.com"

    def chapters(self):
        for tag in self.soup.find_all("div", class_="row"):
            link = tag.span.a
            if not link:
                continue

            chapter, title = RE_CHAPTER.findall(link.text)[0]
            yield {"id": chapter, "title": title, "url": link["href"]}

    def pages(self, soup):
        return [
            tag["src"]
            for tag in soup.find("div", class_="container-chapter-reader").find_all(
                "img", src=True
            )
        ]

    def title(self):
        return self.soup.find("ul", class_="manga-info-text").li.h1.text
