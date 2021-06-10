# coding: utf8

import json
from typing import Dict

from .. import core, models

# from ..exceptions import MangaError

METADATA_MAP = {
    "title": "title",
    "alt_titles": "alt_titles",
    "authors": "authors",
    "genres": "genres",
    "description": "desc",
}


class Parser(core.Parser):

    domain = r"catmanga.org/series/(\w+)"

    # keep state
    # FIXME: cache may grow too large when requesting many manga
    _cache: Dict[str, dict] = {}

    def _get_data(self, url):

        if url not in self._cache:
            soup = self.soup(url)
            # catmanga happens to be a next.js app, so we can use this JSON data.
            # https://github.com/vercel/next.js/discussions/15117
            data = soup.find("script", id="__NEXT_DATA__").string

            self._cache[url] = json.loads(data)["props"]["pageProps"]["series"]

        return self._cache[url]

    def metadata(self, url):
        data = self._get_data(url)

        return models.Metadata(
            url=url,
            cover=data["cover_art"]["source"],
            **{METADATA_MAP[k]: v for k, v in data.items() if k in METADATA_MAP},
        )

    def add_chapters(self, manga):
        data = self._get_data(manga.meta.url)

        for cdata in data["chapters"]:
            cid = str(cdata["number"])

            manga.add(
                models.Chapter(
                    id=cid,
                    url=f"{manga.meta.url}/{cid}",
                    title=cdata.get("title") or "",
                )
            )

    def add_pages(self, chapter):
        soup = self.soup(chapter.url)
        cdata = json.loads(soup.find("script", id="__NEXT_DATA__").string)

        chapter.pages = cdata["props"]["pageProps"]["pages"]
