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
        database["url"] = self.API_URL + f"/manga/{self._id}/chapters"

        self._manga_data = None
        super().__init__(*args, **kwargs)

    def parse_pages(self, soup):
        chapter_data = json.loads(_as_raw(soup))["data"]
        return [
            f"{chapter_data['server']}{chapter_data['hash']}/{u}"
            for u in chapter_data["pages"]
        ]

    def parse_chapters(self):
        if self._manga_data is None:
            self._manga_data = [
                c
                for c in json.loads(_as_raw(self.soup))["data"]["chapters"]
                if c["language"] == "gb"  # multi-language support?
            ]

        for chapter in self._manga_data:
            if chapter.get("volume") == "0":
                chapter["chapter"] = "0"

            yield chapter["chapter"], chapter[
                "title"
            ], self.API_URL + f"/chapter/{chapter['id']}"

    def parse_volumes(self):
        covers = self.session.get(self.API_URL + f"/manga/{self._id}/covers").json()[
            "data"
        ]

        volumes = {}
        previous_volume = None
        for chapter in self._manga_data:
            # some newer chapters don't have the volume attribute
            if chapter["volume"]:
                volume = chapter["volume"]
                previous_volume = volume
            else:
                volume = previous_volume

            volume_info = volumes.setdefault(volume, {"chapters": set()})
            volume_info["chapters"].add(chapter["chapter"])
            volumes[volume] = volume_info

        for cover in covers:
            volumes[cover["volume"]]["cover"] = cover["url"]

        return volumes
