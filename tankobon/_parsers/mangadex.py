# coding: utf8

import json
import re
from urllib.parse import urlparse

from tankobon import manga

BASE_URL = "mangadex.org"
API_URL = f"https://{BASE_URL}/api/v2"
RE_ID = re.compile(r"^/title/(\d+)/(\w+)/?(.*)$")


def _parse_id(url: str) -> str:
    return RE_ID.findall(urlparse(url).path)[0][0]


class Parser(manga.Parser):

    domain = BASE_URL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._id = _parse_id(self.data["url"])

        if not self.data.get("api_url"):
            self.data["api_url"] = f"{API_URL}/manga/{self._id}/chapters"

        with self.session.get(self.data["api_url"]) as response:

            self._manga_data = [
                c
                for c in response.json()["data"]["chapters"]
                if c["language"] == "gb"  # FIXME: multi-language support
            ]
            self._manga_data.reverse()

    def chapters(self):
        previous_volume = "0"
        for chapter in self._manga_data:
            volume = chapter["volume"]
            if not volume:
                volume = previous_volume
            else:
                previous_volume = volume

            if not chapter["chapter"]:
                # oneshot??
                chapter["chapter"] = "0"

            yield {
                "id": chapter["chapter"],
                "title": chapter["title"],
                # NOTE: data_saver is set to true for now (higher-quality image download keeps getting dropped)
                "url": f"{API_URL}/chapter/{chapter['id']}?saver=true",
                "volume": volume,
            }

    def pages(self, soup):
        chapter_data = json.loads(soup.text)["data"]

        chapter_hash = chapter_data["hash"]
        pages = chapter_data["pages"]
        base_url = chapter_data["server"]

        return [f"{base_url}{chapter_hash}/{page}" for page in pages]

    def title(self):
        return self.soup.find("span", class_="mx-1").text
