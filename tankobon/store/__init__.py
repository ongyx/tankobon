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
    # called for every chapter id yielded from parse_chapters, and the soup of its url.
    def parse_pages(self, id, soup):
        ...

See the existing stores in this folder for more details.
"""

import importlib
import json
import logging
import pathlib

from tankobon.base import GenericManga  # noqa: F401

_log = logging.getLogger("tankobon")

STORE_PATH = pathlib.Path(__file__).parent
INDEX = STORE_PATH / "index.json"

STORES = {
    "komi-san.com": "komi_san",
    "m.mangabat.com": "mangabat",
}


class Store(object):
    """Helper to load Manga classes from Stores.

    Usage:

    manga_store = Store('store_name', 'manga_name')
    # the raw Manga object
    Manga = manga_store.manga
    # load database
    manga = Manga(
        manga_store.database,
        ...  # other args
    )

    with Store('store_name', 'manga_name') as manga:
        # use the manga object directly
        manga.parse_all()

    Args:
        store: The store name.
        name: The manga name to get from the store. Defaults to ''.

    Attributes:
        store (str): store name.
        name (str): manga name.
        manga (tankobon.base.GenericManga): The uninitalised Manga class (if you want to subclass).
        available (set): All loadable Stores.
        database: The manga's database.
    """

    available = set()

    for module in STORE_PATH.glob("*.py"):
        if module.stem != "__init__":
            available.add(module.stem)

    with INDEX.open() as f:
        _index = json.load(f)

    def __init__(self, store: str, name: str = "") -> None:
        if store not in self.available:
            raise ValueError(f"store '{store}' does not exist")

        try:
            self._store_module = importlib.import_module(f"tankobon.store.{store}")
        except ModuleNotFoundError as err:
            raise ValueError(f"failed loading store '{store}': {err}")

        self.store = store
        self.name = name
        self.pyfile = STORE_PATH / f"{store}.py"

        _log.debug("initalised store for %s", store)

    @property
    def manga(self) -> type:
        # mypy dosen't like dynamic imports
        return self._store_module.Manga  # type: ignore

    @property
    def database(self):
        return (
            self._index["stores"].setdefault(self.store, {}).setdefault(self.name, {})
        )

    @database.setter
    def database(self, value):
        self._index["stores"][self.store][self.name] = value

    @database.deleter
    def database(self):
        del self._index["stores"][self.store][self.name]

    def close(self):
        with INDEX.open(mode="w") as f:
            json.dump(self._index, f, indent=4)

    def __enter__(self):
        return self.manga(self.database)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
