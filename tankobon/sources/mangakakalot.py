# coding: utf8

import re

from .. import core, models


RE_CHAPTER = re.compile(r".*[Cc]hapter ?([\d\.]+) ?:? ?(.*)")


class Parser(core.Parser):

    domain = r"mangakakalot.com"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._url = None
        self._soup = None

    def _get_soup(self, url):
        if url != self._url:
            self._soup = self.soup(url)

        return self._soup

    def metadata(self, url):
        soup = self._get_soup(url)
        info = soup.find(class_="manga-info-text").find_all("li")

        title_tag = info[0]
        title = title_tag.h1.text

        alt_titles_tag = title_tag.h2.text.partition(":")[-1]
        alt_titles = alt_titles_tag.split(",")

        authors = [a.text for a in info[1].find_all("a")]

        genres = [a.text.lower().replace(" ", "_") for a in info[6].find_all("a")]

        desc_tag = soup.find("div", id=["panel-story-info-description", "noidungm"])

        try:
            desc_tag.p.decompose()
        except AttributeError:
            pass
        finally:
            desc = desc_tag.text

        cover = soup.find("div", class_="manga-info-pic").img["src"]

        return models.Metadata(
            url=url,
            title=title,
            alt_titles=alt_titles,
            authors=authors,
            genres=genres,
            desc=desc,
            cover=cover,
        )

    def add_chapters(self, manga):
        soup = self._get_soup(manga.meta.url)

        for tag in soup.find_all("div", class_="row"):
            link = tag.span.a
            if not link:
                continue

            cid, title = RE_CHAPTER.findall(link.text)[0]

            manga.add(
                models.Chapter(
                    id=cid,
                    url=link["href"],
                    title=title,
                )
            )

    def add_pages(self, chapter):
        soup = self.soup(chapter.url)
        chapter.pages = [
            tag["src"]
            for tag in soup.find("div", class_="container-chapter-reader").find_all(
                "img", src=True
            )
        ]
