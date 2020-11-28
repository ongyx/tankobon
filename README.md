# tankobon
<!-- markdownlint-disable-file MD026 -->

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/logo.jpg "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)

## What?

tankobon is a website scraper for comics and mangas. tankobon relies on **stores**, which define how to parse a website for chapters and chapters for links to the pages themselves.
(somewhat like youtube-dl extractors.) Currently, the following websites are supported:

- `komi-san.com`
- `m.mangabat.com`
- `mangadex.org`

I will eventually come up with documentation later on how to create a store.
See `tankobon/stores/` for these example stores.

## Index Compatibility

Between version v3.1.0a1 and v3.2.0a0, the location of the index file has moved from site-packages to `~/.tankobon/index.json`, specific to each install of tankobon.

## Todo

- download pre-parsed indexes from a special Github repo (tankobon-index?)
- create GUI to make downloading easier (like youtube-DLG)

## Usage

```bash
tankobon download 'https://komi-san.com'  # download all chapters
tankobon store info 'komi_san/https://komi-san.com'  # and then get info on the chapters
```

## Install

`python(3) -m pip install tankobon`

## Build

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
To build, do `flit build`.

## License

MIT.
