# tankobon
<!-- markdownlint-disable-file MD026 -->

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/logo.jpg "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)

## What?

tankobon is a website scraper for comics and mangas. tankobon relies on **stores**, which define how to parse a website for chapters and chapters for links to the pages themselves.
(somewhat like youtube-dl extractors.) Currently, the following websites are supported:

- `komi-san.com`
- `m.mangabat.com`
- `mangadex.org`
- `mangakakalot.com`

## Creating a Store

A store is a regular Python module in the `stores/` folder.
It should provide a `Manga` class, which is a subclass of `tankobon.base.GenericManga`.
The following methods below **must** be implemented:

### `get_chapters(self) -> Generator[Tuple[str, Dict[str, str]], None, None]`

Yield a two-tuple of (chapter_number, chapter_info) where chapter_info looks like this:
```python
{
    "title": ...,  # chapter title
    "url": ...,  # chapter url
    "volume": ...,  # volume, i.e '0'
}
```

Volume may or may not be given; no volume implies volume `0`. Example:

```python
def get_chapters(self):
    # use self.soup to access the title page
    for href in self.soup.find_all("a", href=True):
        # validify href here and parse chapter id
        ...
        yield chapter_id, {"title": href.text, "url": href["href"]}
```

### `get_pages(self, chapter_url: str) -> List[str]`

Return a list of urls to a chapter's pages, given its url.
The pages **must** be in order (page 1 is [0], page 2 is [1], etc.) Example:

```python
def get_pages(self, chapter_url):
    pages = []
    # to get the chapter's html, use self.session.get (requests session)
    # or self.get_soup (html already parsed by BeautifulSoup).
    chapter_page = self.get_soup(chapter_url)
    for href in chapter_page.find_all("a", href=True):
        # validify href here
        ...
        pages.append(href["href"])
    return pages
```

The following methods below _may_ or _may not_ be implemented: generic implementations are provided.

### `get_title(self) -> str`

Return the title of the manga. Example:

```python
def get_title(self):
    return self.soup.title
```

### `get_covers(self) -> Dict[str, str]`

Return a dictionary map of volume (i.e '0', '1') to its cover. Example:

```python
def get_covers(self):
    # The website might have a different api to obtain covers,
    # but we'll just fake one here.

    # (And yes, I do know dictionary comprehensions are better.)
    covers = {}
    for cover in self.soup.find_all("li"):
        covers[cover.a.text] = cover.a["href"]
    
    return covers
```

## Index Compatibility

Between version v3.1.0a1 and v3.2.0a0, the location of the index file has moved from site-packages to `~/.tankobon/index.json`, specific to each install of tankobon.

## Todo

- download pre-parsed indexes from a special Github repo (tankobon-index?)
- create GUI to make downloading easier (like youtube-DLG)

## Usage

```bash
tankobon download 'https://komi-san.com'  # download all chapters
tankobon store info 'komi_san/https://komi-san.com'  # and then get info on the chapters
```

## Install

`python(3) -m pip install tankobon`

## Build

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
To build, do `flit build`.

## License

MIT.
