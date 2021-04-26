# coding: utf8


class TankobonError(Exception):
    pass


class UnknownDomainError(TankobonError):
    pass


class CacheError(TankobonError):
    pass


class MangaNotFoundError(CacheError):
    pass
