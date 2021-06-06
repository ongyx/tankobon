# coding: utf8
"""This directory contains sources for several websites.

Sources are analogous to youtube-dl extractors: they define how to parse out infomation of a manga on a webpage.

Sources contain two classes: parsers and searchers.
Parsers *must* subclass and satisfy the tankobon.manga.Manga interface.

Typically, parsers make heavy use of regexes and leverage the BeautifulSoup API through the .soup attribute:

>>> from tankobon import core
>>>
>>> class MyManga(core.Manga):
...
...     # The domain of the website you are going to parse, *without* a 'www' in front.
...     domain = "my-website.com"
...
...     def chapters(self):
...         chapters = []
...
...         for tag in self.soup.find_all("div"):
...             chapters.append(
...                 manga.Chapter(
...                     id=tag.h1.text,
...                     url=tag.a["href"],
...                     title=tag.h2.text,
...                 )
...             )
...
...         return chapters
...
...     def pages(self, chapter):
...         soup = self.soup_from_url(chapter.url)
...         return [tag["href"] for tag in soup.find_all("a", href=True)]

When subclassed, the new parser will automatically be registered (as long as it runs, i.e import it).
The parser will then be delegated to based on the domain name (using urlparse's netloc).
"""

# import to register default sources
from . import catmanga, mangadex, mangakakalot
