# Table of Contents

* [tankobon.core](#tankobon.core)
  * [Metadata](#tankobon.core.Metadata)
    * [parsed](#tankobon.core.Metadata.parsed)
  * [Chapter](#tankobon.core.Chapter)
  * [Manga](#tankobon.core.Manga)
    * [parser](#tankobon.core.Manga.parser)
    * [from\_url](#tankobon.core.Manga.from_url)
    * [import\_dict](#tankobon.core.Manga.import_dict)
    * [export\_dict](#tankobon.core.Manga.export_dict)
    * [refresh](#tankobon.core.Manga.refresh)
    * [select](#tankobon.core.Manga.select)
    * [soup\_from\_url](#tankobon.core.Manga.soup_from_url)
    * [download](#tankobon.core.Manga.download)
    * [download\_cover](#tankobon.core.Manga.download_cover)
    * [total](#tankobon.core.Manga.total)
    * [metadata](#tankobon.core.Manga.metadata)
    * [chapters](#tankobon.core.Manga.chapters)
    * [pages](#tankobon.core.Manga.pages)
  * [Cache](#tankobon.core.Cache)
    * [save](#tankobon.core.Cache.save)
    * [load](#tankobon.core.Cache.load)
    * [delete](#tankobon.core.Cache.delete)
* [tankobon.utils](#tankobon.utils)
  * [filesize](#tankobon.utils.filesize)
  * [sanitize](#tankobon.utils.sanitize)
  * [get\_soup](#tankobon.utils.get_soup)
  * [save\_response](#tankobon.utils.save_response)
  * [is\_url](#tankobon.utils.is_url)
  * [parse\_domain](#tankobon.utils.parse_domain)

<a name="tankobon.core"></a>
# tankobon.core

Core functionality of tankobon.

<a name="tankobon.core.Metadata"></a>
## Metadata Objects

```python
@dataclass
class Metadata()
```

Helper class to store manga metadata.

**Arguments**:

- `url` - The url to the manga title page.
- `title` - The manga name in English (romanized/translated).
- `alt_titles` - A list of alternative names for the manga.
  i.e in another language, original Japanese name, etc.
- `authors` - A list of author names.
- `genres` - A list of catagories the manga belongs to.
  i.e shounen, slice_of_life, etc.
  Note that the catagories are sanitised using utils.sanitise() on initalisation.
- `desc` - The sypnosis (human-readable info) of the manga.
- `cover` - The url to the manga cover page (must be an image).

<a name="tankobon.core.Metadata.parsed"></a>
#### parsed

```python
 | parsed()
```

Check whether the metadata fields has been partially/totally filled.

<a name="tankobon.core.Chapter"></a>
## Chapter Objects

```python
@dataclass
class Chapter()
```

A manga chapter.

**Arguments**:

- `id` - The chapter id as a string (i.e 1, 2, 10a, etc.).
- `url` - The chapter url.
- `title` - The chapter name.
- `volume` - The volume the chapter belongs to.
- `pages` - A list of image urls to the chapter pages.

<a name="tankobon.core.Manga"></a>
## Manga Objects

```python
class Manga(abc.ABC)
```

A manga hosted somewhere online.

**Attributes**:

- `data` - A map of chapter id to the Chapter object.
- `domain` - The name of the manga host website, i.e 'mangadex.org'.
  This **must** be set in any derived subclasses like so:
  
  class MyManga(Manga):
  domain = 'mymanga.com'
  ...
  
- `hash` - A MD5 checksum of the manga title + url.
  This can be used to uniquely identify manga.
- `meta` - The manga metadata as a Metadata object.
- `registered` - A map of subclass domain to the subclass itself.
  Subclasses can then be delegated to depending on a url's domain.
- `session` - The requests.Session used to download soups.
- `soup` - The BeautifulSoup of the manga title page.

<a name="tankobon.core.Manga.parser"></a>
#### parser

```python
 | @classmethod
 | parser(cls, url: str)
```

Get the appropiate subclass for the domain in url.

**Arguments**:

- `url` - The url to get the subclass for.
  

**Returns**:

  The subclass that can be used to parse the url.
  

**Raises**:

  UnknownDomainError, if there is no registered subclass for the url domain.

<a name="tankobon.core.Manga.from_url"></a>
#### from\_url

```python
 | @classmethod
 | from_url(cls, url: str) -> Manga
```

Parse a url into a Manga object.
The appropiate subclass will be selected based on the url domain.

**Arguments**:

- `url` - The url to parse.
  

**Returns**:

  The parsed Manga object.

<a name="tankobon.core.Manga.import_dict"></a>
#### import\_dict

```python
 | @classmethod
 | import_dict(cls, data: Dict[str, Any]) -> Manga
```

Import manga data.

**Arguments**:

- `data` - The previously exported data from export_dict().

<a name="tankobon.core.Manga.export_dict"></a>
#### export\_dict

```python
 | export_dict() -> Dict[str, Any]
```

Export the manga data.
The dict can be saved to disk and loaded back later using import_dict().

**Returns**:

  The manga data as a dict.

<a name="tankobon.core.Manga.refresh"></a>
#### refresh

```python
 | refresh(pages: bool = False)
```

Refresh the list of chapters available.

**Arguments**:

- `pages` - Whether or not to parse the pages for any new chapters.
  Defaults to False (may take up a lot of bandwidth for many chapters).

<a name="tankobon.core.Manga.select"></a>
#### select

```python
 | select(start: str, end: str) -> List[str]
```

Select chapter ids from the start id to the end id.
The ids are sorted first.

**Arguments**:

- `start` - The start chapter id.
- `end` - The end chapter id.
  

**Returns**:

  A list of all chapter ids between start and end (inclusive of start and end).

<a name="tankobon.core.Manga.soup_from_url"></a>
#### soup\_from\_url

```python
 | soup_from_url(url: str) -> bs4.BeautifulSoup
```

Retreive a url and create a soup using its content.

<a name="tankobon.core.Manga.download"></a>
#### download

```python
 | download(cid: str, to: Union[str, pathlib.Path], progress: Callable[[int], None]) -> List[pathlib.Path]
```

Download a chapter's pages to a folder.

**Arguments**:

- `cid` - The chapter id to download.
- `to` - The folder to download the pages to.
- `progress` - A callback function which is called with the page number every time a page is downloaded.
  

**Returns**:

  A list of absolute paths to the downloaded pages in ascending order
  (1.png, 2.png, 3.png, etc.)
  

**Raises**:

  PagesNotFoundError, if the chapter's pages have not been parsed yet.
  To avoid this, .pages(refresh=True) should be called at least once.

<a name="tankobon.core.Manga.download_cover"></a>
#### download\_cover

```python
 | download_cover() -> requests.Response
```

Download the manga cover.
The manga cover url must be valid.

**Returns**:

  The requests.Response of the manga cover url.

<a name="tankobon.core.Manga.total"></a>
#### total

```python
 | total() -> int
```

Return the total number of pages in this manga.
All the chapter pages must have already been parsed.

<a name="tankobon.core.Manga.metadata"></a>
#### metadata

```python
 | @abc.abstractmethod
 | metadata() -> Metadata
```

Parse metadata from the manga title page.

**Returns**:

  A Metadata object.

<a name="tankobon.core.Manga.chapters"></a>
#### chapters

```python
 | @abc.abstractmethod
 | chapters() -> Generator[Chapter, None, None]
```

Parse chapter info from the manga title page.

**Yields**:

  A Chapter object for each chapter in the manga.

<a name="tankobon.core.Manga.pages"></a>
#### pages

```python
 | @abc.abstractmethod
 | pages(chapter: Chapter) -> List[str]
```

Parse pages (images of the manga) from the manga chapter page.

**Arguments**:

- `chapter` - The Chapter object to parse for.
  

**Returns**:

  A list of urls to the chapter pages (must be images).

<a name="tankobon.core.Cache"></a>
## Cache Objects

```python
class Cache()
```

<a name="tankobon.core.Cache.save"></a>
#### save

```python
 | save(manga: Manga, cover: bool = False)
```

Save this manga within the cache.

**Arguments**:

- `manga` - The manga object to save.
- `cover` - Whether or not to save the cover to the cache (if the cover url exists).
  Defaults to False.

<a name="tankobon.core.Cache.load"></a>
#### load

```python
 | load(url: str)
```

Load a manga by url.

**Arguments**:

- `url` - The manga url.
  

**Returns**:

  The Manga object.
  

**Raises**:

  MangaNotFoundError, if the manga does not exist in the cache.

<a name="tankobon.core.Cache.delete"></a>
#### delete

```python
 | delete(url: str)
```

Delete a manga from the cache.

**Arguments**:

- `url` - The manga url.
  

**Raises**:

  MangaNotFoundError, if the manga does not exist in the cache.

<a name="tankobon.utils"></a>
# tankobon.utils

Utilities for tankobon.

<a name="tankobon.utils.filesize"></a>
#### filesize

```python
filesize(content: bytes) -> str
```

Create a human-readable filesize for content.

**Arguments**:

- `content` - The bytes to get the size of.

**Returns**:

  A string of the filesize ending in B, kB, etc.

<a name="tankobon.utils.sanitize"></a>
#### sanitize

```python
sanitize(name: str) -> str
```

Sanitise a name so it can be used as a filename.

**Arguments**:

- `name` - The name to sanitise.

**Returns**:

  The sanitised name as a string.

<a name="tankobon.utils.get_soup"></a>
#### get\_soup

```python
get_soup(*args, *, encoding: Optional[str] = None, parser: str = BSOUP_PARSER, session: Optional[requests.Session] = None, **kwargs, ,) -> bs4.BeautifulSoup
```

Get a url as a BeautifulSoup.

**Arguments**:

- `*args` - See get_url.
- `encoding` - The encoding to decode.
  Defaults to the autodetected encoding (by requests).
- `parser` - The parser to use.
  Must be 'html.parser', 'html5lib' or 'lxml'.
- `session` - The session to use to download the soup.
  Defaults to None.
- `**kwargs` - See get_url.

<a name="tankobon.utils.save_response"></a>
#### save\_response

```python
save_response(path: pathlib.Path, res: requests.models.Response) -> pathlib.Path
```

Save a Requests response at path with the correct file extension.

**Arguments**:

- `path` - The path where to save the file at.
- `res` - The response.
  

**Returns**:

  The full path to the file.

<a name="tankobon.utils.is_url"></a>
#### is\_url

```python
is_url(url: str) -> bool
```

Check whether or not a string is a url.

<a name="tankobon.utils.parse_domain"></a>
#### parse\_domain

```python
parse_domain(url: str) -> str
```

Parse out a url's domain.

**Arguments**:

- `url` - The url to parse.
  

**Returns**:

  The domain.

