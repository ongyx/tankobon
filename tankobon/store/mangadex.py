# coding: utf8

import collections
import json
import re

from tankobon.base import GenericManga


# the html parser library will correct the JSON to vaild html so we have to get the raw JSON
# idk which parser will be used, so only get the first piece of text.
def _as_raw(soup):
    return str(soup.find(text=True))


class Manga(GenericManga):

    API_URL = "https://mangadex.org/api/v2"
    RE_URL = re.compile(r".*/(\d+)/(\w+)/?.*")

    def __init__(self, *args, **kwargs):
        database = next(iter(args), None) or kwargs.get("database")
        self._id = self.RE_URL.findall(database["url"])[0][0]
        database["url"] = f"{self.API_URL}/manga/{self._id}/chapters"

        self._manga_data = None
        super().__init__(*args, **kwargs)

    def get_pages(self, url):
        chapter_data = self.session.get(url).json()["data"]
        return [
            f"{chapter_data.get('serverFallback') or chapter_data['server']}{chapter_data['hash']}/{u}"
            for u in chapter_data["pages"]
        ]

    def get_chapters(self):
        if self._manga_data is None:
            self._manga_data = [
                c
                for c in json.loads(_as_raw(self.soup))["data"]["chapters"]
                if c["language"] == "gb"  # multi-language support?
            ]

        for chapter in self._manga_data:
            if not chapter.get("volume"):
                chapter["volume"] = "0"

            if chapter["volume"] == "0":
                # oneshot??
                chapter["chapter"] = "0"

            yield chapter["chapter"], {
                "title": chapter["title"],
                # NOTE: data_saver is set to true for now (higher-quality image download keeps getting dropped)
                "url": f"{self.API_URL}/chapter/{chapter['id']}?saver=true",
                "volume": chapter["volume"],
            }

    def get_covers(self):
        covers = self.session.get(f"{self.API_URL}/manga/{self._id}/covers").json()[
            "data"
        ]

        return {cover["volume"]: cover["url"] for cover in covers}
