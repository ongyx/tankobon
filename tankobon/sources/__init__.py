# coding: utf8
"""This directory contains sources for several websites.

Sources are regular modules that have the following classes:

## `Parser`

Subclass of `tankobon.base.Parser`.

`Parser`s must implement the methods `metadata`, `chapters` and `pages`.

It must also have a class attribute `domain`, which is a uncompiled regex pattern of the urls the parser can parse.
At minimum it should be the base of the url (**without** http(s):// or www. in front):

```python
domain = r"my-manga-host.com"
```

These base classes are in the `base.py` file.

When subclassed, the new parser will automatically be registered (as long as it runs, i.e import it).
The parser will then be delegated to based on the domain.

For some examples, take a look at the sources in this directory.

To use a source:

from tankobon import Parser

parser = Parser.by_url(manga_url)
manga = parser.create(manga_url)
"""

# import to register default sources
from . import mangadex, mangakakalot
