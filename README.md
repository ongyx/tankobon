# tankobon

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/logo.jpg "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)

## What?

tankobon is a website scraper for comics and mangas. tankobon relies on **parsers**,
which define how to parse a website for chapters and chapters for links to the pages themselves.
(somewhat like youtube-dl extractors.) Currently, the following websites are supported:

- `mangabat.com`
- `mangadex.org`
- `mangakakalot.com`

## Todo

- download pre-parsed indexes from a special Github repo (tankobon-index?)
- create GUI to make downloading easier (like youtube-DLG)

## Usage

```bash
# do 'tankobon parse' if you don't want to download any chapters
tankobon download 'https://mangadex.org/title/56776/koi-wa-iikara-nemuritai'
# you can also get info by title
tankobon info 'https://mangadex.org/title/56776/koi-wa-iikara-nemuritai'
```

## Install

`pip install tankobon`

## Build

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
To build, do `flit build`.

## License

MIT.
