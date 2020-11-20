# coding: utf8


class TankobonError(Exception):
    pass


class CacheError(TankobonError):
    pass


class StoreError(TankobonError):
    pass