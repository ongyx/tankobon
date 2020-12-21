# coding: utf8

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
        # Manga data has not been initalised, defer update
        do_update = kwargs.get("update") or False
        kwargs["update"] = False
        super().__init__(*args, **kwargs)

        self._id = self.RE_URL.findall(self.database["url"])[0][0]
        if not self.database.get("api_url"):
            self.database["api_url"] = f"{self.API_URL}/manga/{self._id}/chapters"

        self._manga_data = [
            c
            for c in self.session.get(self.database["api_url"]).json()["data"][
                "chapters"
            ]
            if c["language"] == "gb"  # multi-language support?
        ]
        self._manga_data.reverse()

        # update now
        if do_update:
            self.update()

    def get_title(self):
        return self.soup.find("span", class_="mx-1").text

    def get_pages(self, url):
        chapter_data = self.session.get(url).json()["data"]
        return [
            f"{chapter_data.get('serverFallback') or chapter_data['server']}{chapter_data['hash']}/{u}"
            for u in chapter_data["pages"]
        ]

    def get_chapters(self):
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

            yield chapter["chapter"], {
                "title": chapter["title"],
                # NOTE: data_saver is set to true for now (higher-quality image download keeps getting dropped)
                "url": f"{self.API_URL}/chapter/{chapter['id']}?saver=true",
                "volume": volume,
            }

    def get_covers(self):
        covers = self.session.get(f"{self.API_URL}/manga/{self._id}/covers").json()[
            "data"
        ]

        return {cover["volume"]: cover["url"] for cover in covers}
