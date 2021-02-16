# coding: utf8

import re

from tankobon import manga


IMAGE_HOST = "blogspot.com"
RE_TITLE = re.compile(r"(?:.*)Chapter (\d+(?:\.\d)?) *[:\-] *(.+)\Z")
RE_OMAKE = re.compile(r"\d+\.\d")
# not used, kept here for reference
RE_URL = re.compile(r"(?:.*)?chapter-(\d+(?:-\d)?)-([\w\-]*)/?\Z")


class Parser(manga.Parser):

    domain = "komi-san.com"
    DEFAULTS = {
        "title": "Komi Can't Communicate",
        "url": f"https://{domain}",
        "chapters": {},
    }

    def chapters(self):
        # get rid of section
        section = self.soup.find("section", class_="widget ceo_latest_comics_widget")
        if section is not None:
            section.decompose()

        for tag in self.soup.find_all("a", href=True):

            href = str(tag.get("href"))
            title = str(tag.text)

            match = RE_TITLE.findall(title)

            if match:
                chapter, title = match[0]
                yield {"id": chapter, "title": title, "url": href}

    def pages(self, soup):
        # pages_div = soup.find("div", class_="post-body entry-content")
        # if not pages_div:
        #    return

        return [
            link["src"]
            for link in soup.find_all("img", src=True)
            if IMAGE_HOST in link["src"]
        ]

    def title(self):
        return self.DEFAULTS["title"]
