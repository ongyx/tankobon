# coding: utf8

import MangaDexPy as mangadex  # type: ignore

from .. import models
from ..utils import CONFIG
from . import base

CONFIG.setdefault("mangadex.data_saver", False)


# turns something like 'es-la' to 'es'.
def normalize(lang):
    return lang.split("-")[0]


class Parser(base.Parser):

    domain = r"mangadex\.org/title/([a-fA-F0-9\-]+)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = mangadex.MangaDex()
        self._cache = {}

    def _get_manga(self, url):
        manga_id = self.domain.search(url).group(1)

        if manga_id not in self._cache:
            self._cache[manga_id] = self.client.get_manga(manga_id)

        return self._cache[manga_id]

    def metadata(self, url):
        manga = self._get_manga(url)

        alt_titles = []

        for alt_title in manga.titles:
            alt_titles.extend(alt_title.values())

        authors = []

        # NOTE: array keys must have brackets '[]'!
        for author in self.client.search("author", params={"ids[]": manga.author}):
            authors.append(author.name)

        # localised descriptions
        desc = {normalize(k): v for k, v in manga.desc.items()}

        return models.Metadata(
            url=url,
            title=manga.title["en"],
            alt_titles=alt_titles,
            authors=authors,
            genres=[t.name["en"] for t in manga.tags],
            desc=desc,
            cover=self.client.get_cover(manga.cover).url,
        )

    def add_chapters(self, manga):
        manga_resp = self._get_manga(manga.meta.url)

        for chapter in manga_resp.get_chapters():

            manga.add(
                models.Chapter(
                    id=chapter.chapter or "0",
                    url=f"https://mangadex.org/chapter/{chapter.id}",
                    title=chapter.title,
                    volume=chapter.volume,
                    lang=normalize(chapter.language),
                )
            )

    def add_pages(self, chapter):
        uuid = chapter.url.rpartition("/")[-1]

        net_chapter = self.client.get_chapter(uuid).get_md_network()

        if CONFIG["mangadex.data_saver"]:
            # use low-quality images to save bandwidth
            chapter.pages = net_chapter.pages_redux

        else:
            chapter.pages = net_chapter.pages
