# coding: utf8

import re

from tankobon import manga


RE_TITLE = re.compile(r"(.*) Manga *\|")
RE_CHAPTER = re.compile(r"Chapter (\d+)\:? ?([\w \(\)]*)")


class Parser(manga.Parser):

    domain = "mangabat.com"

    def chapters(self):
        for tag in self.soup.find_all("a", class_="chapter-name"):
            href = str(tag.get("href"))
            title = str(tag.text)

            match = RE_CHAPTER.findall(title)

            if match:
                chapter, title = match[0]
                yield {"id": chapter, "title": title, "url": href}

    def pages(self, soup):
        pages_div = soup.find("div", class_="container-chapter-reader")
        if not pages_div:
            return

        return [link["src"] for link in pages_div.find_all("img", src=True)]

    def title(self):
        return RE_TITLE.findall(super().title())[0]

    def description(self):
        desc = self.soup.find("div", class_="panel-story-info-description")
        desc.h3.decompose()
        return desc.get_text(strip=True)
