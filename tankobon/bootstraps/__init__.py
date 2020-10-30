# coding: utf8
"""Bootstraps are scripts used to scrape manga off a webpage.

A manga bootstrap consists of a Python module with a Manga class in this directory
(name.py), corresponding to a JSON file (name.json) in a compressed zipfile
(INDEX.zip) to save space.

`name` is the manga ID, i.e `Manga-Name: with Punctuation!`-> `manga_name_with_punctuation`.
The name must be a valid Python identifier (recommended to use `snake_case`).
(Because it will be imported as a module.)

Example (`name.py`):

```python
from tankobon.base import GenericManga

# Every bootstrap must have a 'Manga' class which inherits from tankobon.base.GenericManga.
# The 'parse_chapters' and 'parse_pages' methods of GenericManga must be overriden.

class Manga(GenericManga):
    def parse_chapters(self):
        ...
    def parse_pages(self, ...):
        ...
```

The `parse_all` method of the Manga class must emit a manifest conforming to the
Manga schema (see tankobon.schema.SCHEMA). It has already been defined in GenericManga,
so most of the time there is no need to override it. It *just* works.
(See documentation for both functions in tankobon.base.GenericManga on how to correctly implement them.)

The emitted manifest should be added to `INDEX.zip` in this directory. If
recompressing, use DEFLATE.
(I should problably add a way to automate this...)

To load an existing bootstrap:

```python
from tankobon.bootstraps import Bootstrap
# load the associated Manga object from the bootstrap.
manga = Bootstrap("manga_name")
# load the existing manifest for the manga (if avaliable).
manifest = bootstraps.retrieve_manifest("manga_name")
```

"""

import importlib
import json
import pathlib
import zipfile

from .. import base

BOOTSTRAP_PATH = pathlib.Path(__file__).parent
INDEX = BOOTSTRAP_PATH / "INDEX.zip"


class Bootstrap(object):
    """Helper to load Manga classes from bootstraps.
    
    Usage:
    
    manga_bootstrap = Bootstrap('manga_name')
    # the raw Manga object
    Manga = manga_bootstrap.manga
    # preinitalised with manifest
    manga = manga_bootstrap(
        ...  # other args
    )
    
    Args:
        name: The bootstrap name.
    
    Attributes:
        name (str): Bootstrap name.
        manga (tankobon.base.GenericManga): The uninitalised Manga class (if you want to subclass).
        available (list): All loadable bootstraps.
    """
    
    available = []

    for pyfile in BOOTSTRAP_PATH.glob("*.py"):
        if not pyfile.stem == "__init__":
            available.append(pyfile.stem)

    def __init__(self, name: str) -> None:
        if name not in self.available:
            raise ValueError(f"bootstrap '{name}' does not exist")

        try:
            self._bootstrap_module = importlib.import_module(
                f"tankobon.bootstraps.{name}")
        except ModuleNotFoundError as err:
            raise ValueError(f"failed loading bootstrap '{name}': {err}")

        self.name = name
        self.pyfile = BOOTSTRAP_PATH / f"{name}.py"

    @property
    def manga(self) -> type:
        return self._bootstrap_module.Manga

    def __call__(self, **kwargs: dict) -> base.GenericManga:
        """Initalise the Manga object using the database loaded from the bootstrap.
        
        Args:
            **kwargs: Passed to the Manga constructor.
        
        Returns:
            The initalised Manga object.
        """

        with zipfile.ZipFile(str(INDEX)) as zf:
            try:
                with zf.open(f"{self.name}.json") as f:
                    manifest = json.load(f)

            except (KeyError, zipfile.BadZipFile):
                # no manifest available, or zipfile is corrupted
                manifest = None

        if manifest is not None:
            return self.manga(manifest, **kwargs)

        return self.manga(**kwargs)

