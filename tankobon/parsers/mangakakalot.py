# coding: utf8

import re

from .. import core


RE_CHAPTER = re.compile(r".*[Cc]hapter ?([\d\.]+) ?:? ?(.*)")


class Manga(core.Manga):

    domain = "mangakakalot.com"

    def metadata(self):
        info = self.soup.find(class_="manga-info-text").find_all("li")

        title_tag = info[0]
        title = title_tag.h1.string

        alt_titles_tag = title_tag.h2.string.partition(":")[-1]
        alt_titles = alt_titles_tag.split(",")

        authors = [a.string for a in info[1].find_all("a")]

        genres = [a.string.lower().replace(" ", "_") for a in info[6].find_all("a")]

        desc_tag = self.soup.find(id=["panel-story-info-description", "noidungm"])
        try:
            desc_tag.p.decompose()
        except AttributeError:
            pass
        finally:
            desc = desc_tag.string

        cover = self.soup.find("div", class_="manga-info-pic").img["src"]

        return core.Metadata(
            url=self.meta.url,
            title=title,
            alt_titles=alt_titles,
            authors=authors,
            genres=genres,
            desc=desc,
            cover=cover,
        )

    def chapters(self):
        for tag in self.soup.find_all("div", class_="row"):
            link = tag.span.a
            if not link:
                continue

            cid, title = RE_CHAPTER.findall(link.string)[0]

            yield core.Chapter(
                id=cid,
                url=link["href"],
                title=title,
            )

    def pages(self, chapter):
        soup = self.soup_from_url(chapter.url)
        return [
            tag["src"]
            for tag in soup.find("div", class_="container-chapter-reader").find_all(
                "img", src=True
            )
        ]
