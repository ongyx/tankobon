# coding: utf8

import json

from .. import core

METADATA_MAP = {
    "title": "title",
    "alt_titles": "alt_titles",
    "authors": "authors",
    "genres": "genres",
    "description": "desc",
}


class Manga(core.Manga):

    domain = "catmanga.org"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _data(self):

        try:
            self._json

        except AttributeError:
            # catmanga happens to be a next.js app, so we can use this JSON data.
            # https://github.com/vercel/next.js/discussions/15117
            data = self.soup.find("script", id="__NEXT_DATA__").string
            self._json = json.loads(data)["props"]["pageProps"]["series"]

        return self._json

    def metadata(self):
        return core.Metadata(
            url=self.meta.url,
            cover=self._data["cover_art"]["source"],
            **{METADATA_MAP[k]: v for k, v in self._data.items() if k in METADATA_MAP},
        )

    def chapters(self):
        for cdata in self._data["chapters"]:
            cid = str(cdata["number"])

            yield core.Chapter(
                id=cid, url=f"{self.meta.url}/{cid}", title=cdata.get("title") or ""
            )

    def pages(self, chapter):
        soup = self.soup_from_url(chapter.url)

        cdata = json.loads(soup.find("script", id="__NEXT_DATA__").string)

        return cdata["props"]["pageProps"]["pages"]
