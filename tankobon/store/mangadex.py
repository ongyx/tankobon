# coding: utf8

import collections
import json
import re

from tankobon.base import GenericManga


class Manga(GenericManga):

    API_URL = "https://mangadex.org/api/v2"
    RE_URL = re.compile(r".*/title/(\d+)/(\w+)/?")

    def __init__(self, *args, **kwargs):
        self._id = self.RE_URL.findall(kwargs["database"]["url"])[0][0]
        self._manga_data = [
            c
            for c in json.loads(soup.head.text)["data"]["chapters"]
            if c["language"] == "gb"
        ]
        kwargs["database"]["url"] = self.API_URL + f"/manga/{self._id}/chapters"
        super().__init__(*args, **kwargs)

    def parse_pages(self, soup):
        chapter_data = json.loads(soup.head.text)["data"]
        return [chapter_data["server"] + u for u in chapter_data["pages"]]

    def parse_chapters(self):
        for chapter in self._manga_data:
            if chapter.get("volume") == "0":
                chapter["chapter"] = "0"

            yield chapter["chapter"], chapter[
                "title"
            ], self.API_URL + f"/chapter/{chapter['id']}"

    def parse_volumes(self):
        volumes = collections.defaultdict(list)
        previous_volume = None
        for chapter in self._manga_data:
            # some newer chapters don't have the volume attribute
            if not chapter["volume"]:
                volume = previous_volume
            else:
                volume = chapter["volume"]

            volumes[volume].append(chapter["chapter"])
