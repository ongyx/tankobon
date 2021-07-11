# coding: utf8

import re

from .. import models
from . import base

RE_TITLE = re.compile(r"^Chapter (\d+): ([\w ']+)(?: \(Part (\d+)\))?$")

URL = "https://genshin.mihoyo.com/en/manga"

TITLE = "Genshin Impact"

DESC = """
Teyvat is a world blessed by the 7 Elemental Archons.

Though the calamity the world suffered has ceased, and the lands have slowly healed,
peace has yet to be restored to Mondstadt, the city of wind.

The domineering Fatui have been oppressing the surrounding city-states,
under the guise of protection, while an ancient darkness is seeking a chance for revenge...
"""

GENRES = [
    "Fantasy",
    "Full Color",
    "Web Comic",
    "Video Games",
    "Magic",
    "Adventure",
    "Official Colored",
]

COVER = "https://webstatic-sea.mihoyo.com/hk4e/upload/fb/en.jpg"

# Mihoyo uses an internal content service based on channel ids.
# 15 happens to be the one used for the manga.
CHANNEL_URL = "https://genshin.mihoyo.com/content/yuanshen/getContentList"
CHANNEL_ID = "15"

CHAPTER_URL = "https://genshin.mihoyo.com/en/manga/detail/{}?mute=1"


class Parser(base.Parser):

    domain = r"genshin\.mihoyo\.com"

    # Since there is only one manga for now, we can store the Nuxt data across instances.
    _data = None

    @property
    def data(self):
        if self._data is None:
            resp = self.session.get(
                CHANNEL_URL,
                params={
                    "channelId": CHANNEL_ID,
                    "pageSize": 1000,
                    "pageNum": 1,
                    "order": "asc",
                },
            )
            self._data = resp.json()["data"]["list"]

        return self._data

    def metadata(self, url):
        data = self.data

        authors = set()

        for chapter in data:
            if chapter["author"]:
                authors.add(chapter["author"])

        return models.Metadata(
            url=URL,
            title=TITLE,
            alt_titles=[],
            desc={"en": DESC},
            cover=COVER,
            authors=list(authors),
            genres=GENRES,
        )

    def add_chapters(self, manga):
        for chapter in self.data:

            title = chapter["title"]

            if "Prologue" in title:
                cid = "0"

            else:
                match = RE_TITLE.match(title)
                number, title, part = match.groups()

                cid = number + (f".{part}" if part else "")

            pages = chapter["ext"][0]["value"]

            manga.add(
                models.Chapter(
                    id=cid,
                    url=CHAPTER_URL.format(chapter["contentId"]),
                    title=title,
                    # add the pages immediately
                    pages=[page["url"] for page in pages],
                )
            )

    def add_pages(self, chapter):
        pass
