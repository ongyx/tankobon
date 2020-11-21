# coding: utf8
"""Stores are the tankobon equivalent of youtube-dl extractors.
Each store is registered to a specific website (see tankobon.store.STORES).

A store consists of a Python module in this directory.
The module's name should be a normalised version of the website, i.e komi-san.com -> komi_san.py.
Example:

class Manga(GenericManga):
    # must yield a three-tuple of (chapter_id, chapter_title, chapter_url).
    def parse_chapters(self):
        ...
    # must return a list of page urls where soup is the BeautifulSoup of the chapter
    # url.
    def parse_pages(self, soup):
        ...
    # get the cover of the manga, must be a property
    # optional
    @property
    def cover(self):
        ...

See the existing stores in this folder for more details.
"""

import importlib
import logging
import pathlib
from typing import Optional, Union

import json
from tankobon.base import GenericManga  # noqa: F401
from tankobon.exceptions import StoreError

_log = logging.getLogger("tankobon")

STORE_PATH = pathlib.Path.home() / ".tankobon"
INDEX = STORE_PATH / "index.json"

STORES = {
    "komi-san.com": "komi_san",
    "m.mangabat.com": "mangabat",
}

STORE_PATH.mkdir(exist_ok=True)


class Store(object):
    """Helper to load Manga classes from Stores.

    Usage:

    manga_store = Store('store_name', 'manga_name')
    Manga = manga_store.manga  # the raw Manga object
    manga = Manga(manga_store.database)  # load database

    with Store('store_name', 'manga_name') as manga:
        manga.parse_all()  # use the manga object directly

    Args:
        store: The store name.
        name: The manga name to get from the store. This should be the manga url.
        index_path: The path to the index file. Defaults to INDEX.

    Attributes:
        store (str): store name.
        name (str): manga name.
        manga (tankobon.base.GenericManga): The uninitalised Manga class (if you want to subclass).
        available (set): All loadable Stores.
        database: The manga's database.
    """

    available = set()

    for module in pathlib.Path(__file__).parent.glob("*.py"):
        if module.stem != "__init__":
            available.add(module.stem)

    # preload first, so we don't have to load again every time this is initalised
    _index_path = INDEX
    try:
        with _index_path.open() as f:
            _index = json.load(f)
    except FileNotFoundError:
        _index = {}

    def __init__(
        self,
        store: str,
        name: str = "",
        index_path: Optional[Union[str, pathlib.Path]] = None,
    ) -> None:
        if store not in self.available:
            raise ValueError(f"store '{store}' does not exist")

        try:
            self._store_module = importlib.import_module(f"tankobon.store.{store}")
        except ModuleNotFoundError as err:
            raise ValueError(f"failed loading store '{store}': {err}")

        self.store = store
        self.name = name
        self.pyfile = STORE_PATH / f"{store}.py"

        if index_path is not None:
            self._index_path = pathlib.Path(index_path)
            self._index = json.load(self._index_path.open())

        _log.debug("initalised store for %s", store)

    @property
    def manga(self) -> type:
        # mypy dosen't like dynamic imports
        return self._store_module.Manga  # type: ignore

    @property
    def database(self):
        database = self._index.setdefault(self.store, {}).setdefault(self.name, {})
        if not database.get("url"):
            database["url"] = self.name
        return database

    @database.setter
    def database(self, value):
        self._index[self.store][self.name] = value

    @database.deleter
    def database(self):
        del self._index[self.store][self.name]

    def close(self):
        with self._index_path.open(mode="w") as f:
            json.dump(self._index, f, indent=2)

    def __enter__(self):
        return self.manga(self.database)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
