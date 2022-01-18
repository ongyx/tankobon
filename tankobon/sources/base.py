# coding: utf8
"""Abstract base classes for implementing a source."""

from __future__ import annotations

import abc
import re
from typing import List, Type

import bs4

from .. import imposter, models
from ..exceptions import UnknownDomainError


class Parser(abc.ABC):

    # This allows subclasses to be registered.
    registered: List[Type[Parser]] = []

    def __init__(self):
        self.session = imposter.UserSession()

    def create(self, url: str) -> models.Manga:
        """Create a new manga.

        Args:
            url: The manga url.

        Returns:
            A Manga object.
        """

        metadata = self.metadata(url)
        return models.Manga(metadata)

    @classmethod
    def by_url(cls, url: str) -> Parser:
        """Get the appropiate parser subclass for the domain in url.

        Args:
            url: The url to get the subclass for.

        Returns:
            The subclass instance that can be used to parse the url.

        Raises:
            UnknownDomainError, if there is no registered subclass for the url domain.
        """

        for subclass in cls.registered:
            if subclass.domain.search(url):  # type: ignore
                return subclass()

        raise UnknownDomainError(f"no source found for url '{url}'")

    @property
    @abc.abstractmethod
    def domain(self) -> str:
        pass

    @abc.abstractmethod
    def metadata(self, url: str) -> models.Metadata:
        """Parse metadata for a manga url.

        Args:
            url: The manga url.

        Returns:
            The Metadata object.
        """

    @abc.abstractmethod
    def add_chapters(self, manga: models.Manga):
        """Add chapters to the manga.

        This method should add every chapter in the manga as a Chapter object:

        ```python
        def chapters(self, manga):
            for ... in ...:
                # do your parsing here
                manga.add(Chapter(...))
        ```

        Only the 'url' and 'id' args are required when creating a Chapter.
        The other fields are optional and have default values (see `help(tankobon.models.Chapter)`).

        Args:
            manga: The manga object.
        """

    @abc.abstractmethod
    def add_pages(self, chapter: models.Chapter):
        """Add pages to the chapter in the manga as a list of urls.
        The pages must be in ascending order.

        This method should assign pages to the chapter:

        ```python
        def pages(self, chapter):
            # do your parsing here
            chapter.pages = [...]  # assign directly to the chapter's pages.
        ```

        Args:
            chapter: The chapter object (already added to the manga).
        """

    def soup(self, url: str) -> bs4.BeautifulSoup:
        """Get a soup from a url.

        Args:
            url: The url to get a soup from.

        Returns:
            The soup of the url.
        """

        return utils.soup(url, session=self.session)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.domain = re.compile(cls.domain)
        cls.registered.append(cls)
