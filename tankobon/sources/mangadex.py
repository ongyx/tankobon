# coding: utf8

import MangaDexPy  # type: ignore

from .. import core


class Manga(core.Manga):

    # mangadex has no website frontend yet, match base url plus manga id
    domain = r"mangadex\.org/([a-fA-F0-9\-]+)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._chapters = {}

        manga_id = self.domain.search(self.meta.url).group(1)

        self.client = MangaDexPy.MangaDex()
        self.manga = self.client.get_manga(manga_id)

    def metadata(self):

        alt_titles = []

        for alt_title in self.manga.titles:
            alt_titles.extend(alt_title.values())

        authors = []

        # NOTE: array keys must have brackets '[]'!
        for author in self.client.search("author", params={"ids[]": self.manga.author}):
            authors.append(author.name)

        return core.Metadata(
            url=self.meta.url,
            title=self.manga.title["en"],
            alt_titles=alt_titles,
            authors=authors,
            genres=[t.name["en"] for t in self.manga.tags],
            desc=self.manga.desc["en"],
            cover=self.client.get_cover(self.manga.cover).url,
        )

    def chapters(self):
        for chapter in self.manga.get_chapters():

            # FIXME: il8n?
            if chapter.language == "en":

                # store the MangaDex chapter by its id
                self._chapters[chapter.chapter] = chapter

                yield core.Chapter(
                    id=chapter.chapter,
                    # unused
                    url="",
                    title=chapter.title,
                    volume=chapter.volume,
                )

    def pages(self, chapter):
        if chapter.id not in self._chapters:
            chapter_obj = self.client.search(
                "chapter",
                params={
                    "chapter": chapter.id,
                    "translatedLanguage[]": ["en"],
                    "manga": self.manga.id,
                },
            )[0]
        else:
            chapter_obj = self._chapters[chapter.id]

        net_chapter = chapter_obj.get_md_network()

        return net_chapter.pages
