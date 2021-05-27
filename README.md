# tankobon

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/resources/logo.jpg "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)

## What?

tankobon is (somewhat) like youtube-dl for manga websites: it aims to make creating parsers for manga hosting websites easy.

(Plus, it and its dependencies are pure Python!)

Currently, the following websites are supported (rip mangadex, hope we'll see you soon):

- `catmanga.org`
- `mangakakalot.com`

## API Docs

See [here](API.md).

## Usage (CLI)

```bash
# Add a manga url to the cache (at ~/.tankobon):
tankobon refresh https://catmanga.org/series/komi

# Then download it (to the current folder)...
tankobon download https://catmanga.org/series/komi

# ...and pack it into a nice pdf file for use with your favourite e-reader.
tankobon pdfify -o komi.pdf
```

Or maybe you might want to use the GUI instead:

```bash
tankobon gui
```

What it can do:

- Add/refresh/delete manga
- Show HTML-based previews of the manga cover, description, etc.
- Download manga

What it can't do:

- Show manga pages (pdf reader?)

## Todo

- [ ] tests and docs (docs done)
- [x] create GUI to make downloading easier, like youtube-DLG

## Install

`pip install tankobon`

## Build

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
To build, do `flit build`.

## License

MIT.
