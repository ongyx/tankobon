# Table of Contents

* [tankobon.core](#tankobon.core)
  * [Cache](#tankobon.core.Cache)
    * [fullhash](#tankobon.core.Cache.fullhash)
    * [dump](#tankobon.core.Cache.dump)
    * [load](#tankobon.core.Cache.load)
    * [delete](#tankobon.core.Cache.delete)
  * [Downloader](#tankobon.core.Downloader)
    * [downloaded](#tankobon.core.Downloader.downloaded)
    * [download](#tankobon.core.Downloader.download)
    * [download\_cover](#tankobon.core.Downloader.download_cover)
    * [pdfify](#tankobon.core.Downloader.pdfify)
* [tankobon.exceptions](#tankobon.exceptions)
* [tankobon.iso639](#tankobon.iso639)
* [tankobon.models](#tankobon.models)
  * [Metadata](#tankobon.models.Metadata)
  * [Chapter](#tankobon.models.Chapter)
  * [Manga](#tankobon.models.Manga)
    * [add](#tankobon.models.Manga.add)
    * [remove](#tankobon.models.Manga.remove)
    * [exists](#tankobon.models.Manga.exists)
    * [dump](#tankobon.models.Manga.dump)
    * [load](#tankobon.models.Manga.load)
    * [summary](#tankobon.models.Manga.summary)
    * [select](#tankobon.models.Manga.select)
    * [parsed](#tankobon.models.Manga.parsed)
* [tankobon.utils](#tankobon.utils)
  * [filesize](#tankobon.utils.filesize)
  * [sanitize](#tankobon.utils.sanitize)
  * [soup](#tankobon.utils.soup)
  * [save\_response](#tankobon.utils.save_response)
  * [is\_url](#tankobon.utils.is_url)
  * [parse\_domain](#tankobon.utils.parse_domain)
  * [PersistentDict](#tankobon.utils.PersistentDict)
* [tankobon.imposter](#tankobon.imposter)
  * [UserAgent](#tankobon.imposter.UserAgent)
    * [random](#tankobon.imposter.UserAgent.random)
    * [cache](#tankobon.imposter.UserAgent.cache)
  * [cached](#tankobon.imposter.cached)
  * [UserSession](#tankobon.imposter.UserSession)
* [tankobon.sources.base](#tankobon.sources.base)
  * [Parser](#tankobon.sources.base.Parser)
    * [create](#tankobon.sources.base.Parser.create)
    * [by\_url](#tankobon.sources.base.Parser.by_url)
    * [metadata](#tankobon.sources.base.Parser.metadata)
    * [add\_chapters](#tankobon.sources.base.Parser.add_chapters)
    * [add\_pages](#tankobon.sources.base.Parser.add_pages)
    * [soup](#tankobon.sources.base.Parser.soup)

<a id="tankobon.core"></a>

# tankobon.core

Core functionality of tankobon.

<a id="tankobon.core.Cache"></a>

## Cache Objects

```python
class Cache(utils.PersistentDict)
```

A manga cache.

**Arguments**:

- `root` - The root of the cache.
  

**Attributes**:

- `root` - See args.
- `alias` - A map of manga url to manga hash.

<a id="tankobon.core.Cache.fullhash"></a>

#### fullhash

```python
def fullhash(part: str) -> str
```

Get the full SHA512 hash of a manga when only given at least the first 8 letters of the hash.

**Arguments**:

- `part` - The first 8 letters of the hash.
  

**Returns**:

  The full hash, or an empty string if part was not found.
  

**Raises**:

  ValueError, if the length part is less than 8.

<a id="tankobon.core.Cache.dump"></a>

#### dump

```python
def dump(manga: models.Manga)
```

Save this manga within the cache.

**Arguments**:

- `manga` - The manga object to save.

<a id="tankobon.core.Cache.load"></a>

#### load

```python
def load(hash: str) -> models.Manga
```

Load a manga by its hash.

**Arguments**:

- `hash` - The manga hash.
  

**Returns**:

  The Manga object.
  

**Raises**:

  MangaNotFoundError, if the manga does not exist in the cache.

<a id="tankobon.core.Cache.delete"></a>

#### delete

```python
def delete(hash: str)
```

Delete a manga from the cache.

**Arguments**:

- `hash` - The manga hash.
  

**Raises**:

  MangaNotFoundError, if the manga does not exist in the cache.

<a id="tankobon.core.Downloader"></a>

## Downloader Objects

```python
class Downloader()
```

A manga downloader.

**Arguments**:

- `path` - The path to where the manga chapters will be downloaded.
  For every manga chapter, a corrosponding folder is created if it does not exist.

<a id="tankobon.core.Downloader.downloaded"></a>

#### downloaded

```python
def downloaded(chapter: models.Chapter) -> bool
```

Check whether a chapter has been downloaded or not.

<a id="tankobon.core.Downloader.download"></a>

#### download

```python
def download(chapter: models.Chapter, *, force: bool = False, progress: Optional[Callable[[int], None]] = None)
```

Download pages for a chapter.

**Arguments**:

- `chapter` - The Chapter object to download.
- `force` - Whether or not to re-download the chapter if it already exists.
  Defaults to False.
- `progress` - A callback function which is called with the page number every time a page is downloaded.
  Defaults to None.
  

**Raises**:

  PagesNotFoundError, if the chapter to be downloaded has no pages.

<a id="tankobon.core.Downloader.download_cover"></a>

#### download\_cover

```python
def download_cover(manga: models.Manga)
```

Download a manga's cover to the download path as 'cover.(ext)'.

**Arguments**:

- `manga` - The manga to download a cover for.

<a id="tankobon.core.Downloader.pdfify"></a>

#### pdfify

```python
def pdfify(chapters: List[str], dest: Union[str, pathlib.Path], lang: str = "en")
```

Create a PDF out of several (downloaded) chapters.
The PDF will be A4 sized (vertical).

**Arguments**:

- `chapters` - The chapters to create a PDF for.
- `lang` - The language of the chapters.
  Defaults to 'en'.
- `dest` - Where to write the PDF to.

<a id="tankobon.exceptions"></a>

# tankobon.exceptions

<a id="tankobon.iso639"></a>

# tankobon.iso639

ISO 639-1/2 language code dataset mapping.
Dataset sourced from https://github.com/haliaeetus/iso-639.

<a id="tankobon.models"></a>

# tankobon.models

Model classes.

<a id="tankobon.models.Metadata"></a>

## Metadata Objects

```python
@dataclass
class Metadata()
```

Metadata for a manga.

**Arguments**:

- `url` - The url to the manga title page.
- `title` - The manga name in English (romanized/translated).
- `alt_titles` - A list of alternative names for the manga.
  i.e in another language, original Japanese name, etc.
- `desc` - The sypnosis (human-readable info) of the manga.
  This is a map of the ISO 639-1 language code to the localised description.
  At least 'en' (English) should be present.
- `cover` - The url to the manga cover page (must be an image).
- `authors` - A list of author names.
- `genres` - A list of catagories the manga belongs to.
  i.e shounen, slice_of_life, etc.
  Note that the catagories are sanitised using utils.sanitise() on initalisation.
- `other` - Miscellanious map of keys to values.
  May be used by parsers to store parser-specific info (keep state).
  

**Attributes**:

- `hash` - A SHA-256 checksum of the manga url.
  (Can be used for filename-safe manga storage.)

<a id="tankobon.models.Chapter"></a>

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
- `lang` - The RFC 5646 (IETF) language code that this chapter was translated to.
  (i.e 'en' - English)
- `pages` - A list of image urls to the chapter pages.
- `other` - Miscellanious map of keys to values.
  May be used by parsers to store parser-specific info (keep state).

<a id="tankobon.models.Manga"></a>

## Manga Objects

```python
class Manga()
```

A manga.

Selecting chapters in this manga can be done by slicing:

manga[start_cid:end_cid:lang]  # returns a list of Chapter objects

where start_cid is the first chapter of the selection, and end_cid is the last chapter of the selection.
lang is the ISO 639-1 language code of the chapters to select. i.e:

# Select chapters 1 to 5 in the Spanish language (inclusive of chapter 5).
# NOTE: If the chapter does not have a translation for the selected language,
# the number of chapters you get may not be the number requested!
chapters = manga["1":"5":"es"]

**Arguments**:

- `meta` - The manga metadata.
- `chapters` - The manga chapters.
  

**Attributes**:

- `chapters` - A map of chapter ids to a map of ISO 639-1 language codes to Chapter objects (chapters may have several languages):
  
  {
  // chapter id
- `"1"` - {
  // ISO 639-1 language code
- `"en"` - Chapter(...)
  }
  }
  
- `info` - A dictionary which has the following keys:
  
  chapters (int)
  The total number of chapters across all languages.
  
  volumes (set)
  The volumes that this manga has across all languages.
  
  langs (set)
  ISO 639-1 language codes that this manga was translated to.
  Note that chapters may not have a translation for all language codes.

<a id="tankobon.models.Manga.add"></a>

#### add

```python
def add(chapter: Chapter)
```

Add a chapter to this manga.
The chapter will not be added if it already exists (has the same id and lang as the existing one).

**Arguments**:

- `chapter` - The chapter to add.

<a id="tankobon.models.Manga.remove"></a>

#### remove

```python
def remove(cid: str, lang: str = "en") -> Chapter
```

Remove a chapter from this manga.

**Arguments**:

- `cid` - The chapter id to remove.
- `lang` - The chapter language to remove.
  Defaults to 'en'.
  

**Returns**:

  The removed chapter.

<a id="tankobon.models.Manga.exists"></a>

#### exists

```python
def exists(chapter: Chapter) -> bool
```

Check whether a chapter already exists in this manga.

**Arguments**:

- `chapter` - The chapter object.
  

**Returns**:

  True if it exists, otherwise False.

<a id="tankobon.models.Manga.dump"></a>

#### dump

```python
def dump() -> dict
```

Serialise this manga to a dict.

<a id="tankobon.models.Manga.load"></a>

#### load

```python
@classmethod
def load(cls, data: dict) -> Manga
```

Deserialise this manga from a dict.

**Arguments**:

- `data` - The serialised manga.
  

**Returns**:

  The Manga object.

<a id="tankobon.models.Manga.summary"></a>

#### summary

```python
def summary(lang: str = "en", link: bool = True) -> str
```

Create a Markdown table summary of all volumes and chapters in this manga.

**Arguments**:

- `lang` - The language to summerise for.
- `link` - Whether or not to add URL links.
  Defaults to True.
  

**Returns**:

  The Markdown table as a string.

<a id="tankobon.models.Manga.select"></a>

#### select

```python
def select(cids: str, lang: str = "en") -> List[Chapter]
```

Select chapters from this manga.

**Arguments**:

- `cids` - A list of chapter ids as a string, delimited by a comma.
  Ranges are also valid (1-5).
  i.e '1,3,5,8-10' (select chapters 1,3,5 and 8-10 inclusive of 10).
- `lang` - The language of the chapters.
  Note that if a chapter does not have the language requested, it will be skipped.
  

**Returns**:

  A list of Chapter objects.

<a id="tankobon.models.Manga.parsed"></a>

#### parsed

```python
def parsed() -> bool
```

Check whether this manga has been parsed (has at least one chapter).

<a id="tankobon.utils"></a>

# tankobon.utils

Utilities for tankobon.

<a id="tankobon.utils.filesize"></a>

#### filesize

```python
def filesize(content: bytes) -> str
```

Create a human-readable filesize for content.

**Arguments**:

- `content` - The bytes to get the size of.

**Returns**:

  A string of the filesize ending in B, kB, etc.

<a id="tankobon.utils.sanitize"></a>

#### sanitize

```python
def sanitize(name: str) -> str
```

Sanitise a name so it can be used as a filename.

**Arguments**:

- `name` - The name to sanitise.

**Returns**:

  The sanitised name as a string.

<a id="tankobon.utils.soup"></a>

#### soup

```python
def soup(url: str, *args, *, session: Optional[requests.Session] = None, **kwargs) -> bs4.BeautifulSoup
```

Get a url as a BeautifulSoup.

**Arguments**:

- `url` - The url to get a soup from.
- `*args` - Passed to session.get().
- `session` - The session to use to download the soup.
  Defaults to None.
- `**kwargs` - Passed to session.get().

<a id="tankobon.utils.save_response"></a>

#### save\_response

```python
def save_response(path: pathlib.Path, res: requests.models.Response) -> pathlib.Path
```

Save a Requests response at path with the correct file extension.

**Arguments**:

- `path` - The path where to save the file at.
- `res` - The response.
  

**Returns**:

  The full path to the file.

<a id="tankobon.utils.is_url"></a>

#### is\_url

```python
def is_url(url: str) -> bool
```

Check whether or not a string is a url.

<a id="tankobon.utils.parse_domain"></a>

#### parse\_domain

```python
def parse_domain(url: str) -> str
```

Parse out a url's domain.

**Arguments**:

- `url` - The url to parse.
  

**Returns**:

  The domain.

<a id="tankobon.utils.PersistentDict"></a>

## PersistentDict Objects

```python
class PersistentDict(collections.UserDict)
```

A UserDict that can be loaded and dumped to disk persistently.
(As long as the dictionary contents can be serialised to JSON.)

Usage:

```python
from tankobon.utils import PersistentDict

file = "test.json"

with PersistentDict(file) as d:
    d["foo"] = "bar"

# '/where/to/save.json' now looks like this:
# {
#     "foo": "bar"
# }

# It can also be used without a context manager.
# Just remember to sync() or close() it, or any changes won't be written to disk!

d = PersistentDict(file)
d["baz"] = 42
d.sync()

# other operations...

d.close()
```

<a id="tankobon.imposter"></a>

# tankobon.imposter

Imposter fakes a user agent to use in requests.
A random user agent is chosen using a weighted statistic, but if stats are unavailable a non-weighted random is chosen.

<a id="tankobon.imposter.UserAgent"></a>

## UserAgent Objects

```python
@jsonclasses.dataclass
class UserAgent()
```

An interface to get a randomised user agent.

**Attributes**:

- `browsers` - A map of browser name to the possible user agent strings for that browser.
- `stats` - A map of browser name to its vistor statistics retreived from W3Schools.

<a id="tankobon.imposter.UserAgent.random"></a>

#### random

```python
def random(browser: Optional[str] = None, weighted: bool = True) -> str
```

Get a randomised user agent.

**Arguments**:

- `browser` - The browser to limit the user agent to.
- `weighted` - Whether or not to get a random browser by weighted statistic.
  If false, a non-weighted random choice is made.
  

**Returns**:

  The random user agent, as a string.

<a id="tankobon.imposter.UserAgent.cache"></a>

#### cache

```python
def cache()
```

Save the downloaded user agent data to disk.

<a id="tankobon.imposter.cached"></a>

#### cached

```python
def cached() -> UserAgent
```

Load the cached user agent data from disk.

<a id="tankobon.imposter.UserSession"></a>

## UserSession Objects

```python
class UserSession(requests.Session)
```

requests.Session with randomised user agent in the headers.

<a id="tankobon.sources.base"></a>

# tankobon.sources.base

Abstract base classes for implementing a source.

<a id="tankobon.sources.base.Parser"></a>

## Parser Objects

```python
class Parser(abc.ABC)
```

<a id="tankobon.sources.base.Parser.create"></a>

#### create

```python
def create(url: str) -> models.Manga
```

Create a new manga.

**Arguments**:

- `url` - The manga url.
  

**Returns**:

  A Manga object.

<a id="tankobon.sources.base.Parser.by_url"></a>

#### by\_url

```python
@classmethod
def by_url(cls, url: str) -> Parser
```

Get the appropiate parser subclass for the domain in url.

**Arguments**:

- `url` - The url to get the subclass for.
  

**Returns**:

  The subclass instance that can be used to parse the url.
  

**Raises**:

  UnknownDomainError, if there is no registered subclass for the url domain.

<a id="tankobon.sources.base.Parser.metadata"></a>

#### metadata

```python
@abc.abstractmethod
def metadata(url: str) -> models.Metadata
```

Parse metadata for a manga url.

**Arguments**:

- `url` - The manga url.
  

**Returns**:

  The Metadata object.

<a id="tankobon.sources.base.Parser.add_chapters"></a>

#### add\_chapters

```python
@abc.abstractmethod
def add_chapters(manga: models.Manga)
```

Add chapters to the manga.

This method should add every chapter in the manga as a Chapter object:


Only the 'url' and 'id' args are required when creating a Chapter.
The other fields are optional and have default values (see `help(tankobon.models.Chapter)`).

```python
def chapters(self, manga):
    for ... in ...:
        # do your parsing here
        manga.add(Chapter(...))
```

**Arguments**:

- `manga` - The manga object.

<a id="tankobon.sources.base.Parser.add_pages"></a>

#### add\_pages

```python
@abc.abstractmethod
def add_pages(chapter: models.Chapter)
```

Add pages to the chapter in the manga as a list of urls.
The pages must be in ascending order.

This method should assign pages to the chapter:


```python
def pages(self, chapter):
    # do your parsing here
    chapter.pages = [...]  # assign directly to the chapter's pages.
```

**Arguments**:

- `chapter` - The chapter object (already added to the manga).

<a id="tankobon.sources.base.Parser.soup"></a>

#### soup

```python
def soup(url: str) -> bs4.BeautifulSoup
```

Get a soup from a url.

**Arguments**:

- `url` - The url to get a soup from.
  

**Returns**:

  The soup of the url.

