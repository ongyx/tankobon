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
It should provide a `Parser` class, which is a subclass of `tankobon.manga.Parser`.
The following methods below **must** be implemented:

### `chapters(self) -> Generator[Tuple[str, Dict[str, str]], None, None]`

Yields chapter_info which looks like this:
```python
{
    "id": ...,  # chapter number
    "title": ...,  # chapter title
    "url": ...,  # chapter url
    "volume": ...,  # volume, i.e '0'
}
```

Volume is optional and may be undefined. Example:

```python
def chapters(self):
    # use self.soup to access the title page
    for href in self.soup.find_all("a", href=True):
        # validify href here and parse chapter id
        ...
        yield {"id": ..., "title": href.text, "url": href["href"]}
```

### `pages(self, chapter_data: Dict[str, str]) -> List[str]`

Return a list of urls to a chapter's pages, given the chapter data yielded from `chapters()`.
The pages **must** be in order (page 1 is [0], page 2 is [1], etc.) Example:

```python
def pages(self, chapter_data):
    pages = []
    # to get the chapter's html, use self.session.get (requests session)
    # or self.soup (html already parsed by BeautifulSoup).
    chapter_page = self.soup_from_url(chapter_data["url"])

    for href in chapter_page.find_all("a", href=True):
        # validify href here
        ...
        pages.append(href["href"])
    return pages
```

The following methods below _may_ or _may not_ be implemented: generic implementations are provided.

### `title(self) -> str`

Return the title of the manga. Example:

```python
def title(self):
    return self.soup.title
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
