# coding: utf8

import MangaDexPy  # type: ignore

from .. import core, models


class Parser(core.Parser):

    # mangadex has no website frontend yet, match base url plus manga id
    domain = r"mangadex\.org/([a-fA-F0-9\-]+)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = MangaDexPy.MangaDex()
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

        return models.Metadata(
            url=url,
            title=manga.title["en"],
            alt_titles=alt_titles,
            authors=authors,
            genres=[t.name["en"] for t in manga.tags],
            desc=manga.desc["en"],
            cover=self.client.get_cover(manga.cover).url,
        )

    def add_chapters(self, manga):
        manga_resp = self._get_manga(manga.meta.url)

        for chapter in manga_resp.get_chapters():

            # FIXME: il8n?
            if chapter.language == "en":

                manga.add(
                    models.Chapter(
                        id=chapter.chapter or "0",  # the chapter number
                        url=chapter.id,  # the mangadex chapter UUID
                        title=chapter.title,
                        volume=chapter.volume,
                    )
                )

    def add_pages(self, chapter):
        net_chapter = self.client.get_chapter(chapter.url).get_md_network()

        chapter.pages = net_chapter.pages
