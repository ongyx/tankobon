# coding: utf8


class TankobonError(Exception):
    pass


class MangaError(TankobonError):
    pass


class MangaNotFoundError(MangaError):
    pass


class PagesNotFoundError(MangaError):
    pass


class UnknownDomainError(TankobonError):
    pass
