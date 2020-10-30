# coding: utf8

import json
import pathlib

from .base import Cache

CACHEPATH = pathlib.Path.home() / "Documents" / "tankobon"
BOOTSTRAP_PATH = pathlib.Path(__file__).parent / "bootstraps"


def main():
    with (BOOTSTRAP_PATH / "komi_san_wa_komyushou_desu.json").open() as f:
        cache = Cache(CACHEPATH, database=json.load(f))
        cache.download_chapters()


if __name__ == "__main__":
    main()
