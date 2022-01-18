# ![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/.github/logo.jpg) tankobon

![gui](https://raw.githubusercontent.com/ongyx/tankobon/master/example.png "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)
![calver](https://img.shields.io/badge/calver-YY.MM.MICRO-22bfda.svg)

Pure-python manga downloader.

The following websites are currently supported:

- `mangakakalot.com`
- `mangadex.org`

## API Docs / Changelog

See [here](API.md) and [there](CHANGELOG.md).

## Usage (CLI)

```bash
# Add a manga url to the cache (at ~/.local/share/tankobon)
$ tankobon add https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8

# List all manga in the cache
$ tankobon list
supported websites: mangadex\.org/title/([a-fA-F0-9\-]+)
                    mangakakalot.com

540a94ad: Komi-san wa Komyushou Desu. (https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8)

# download it to disk...
$ tankobon download 540a94ad

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

## Multilingual Support

tankobon now supports manga with multiple language translations (especially for Mangadex)!

## Configuration (CLI)

First check the languages the manga supports:

```bash
$ tankobon info <shorthash> | grep languages -A10
...
languages: čeština, český jazyk (cs)
           English (en)
           Italiano (it)
           Русский (ru)
           Español (es)
           Português (pt)
           Bahasa Indonesia (id)
           język polski, polszczyzna (pl)
           Nederlands, Vlaams (nl)
           français, langue française (fr)
```

Next, set the language:

```bash
$ tankobon config lang <code>
```

where code is the two-letter ISO 639-1 id (i.e `fr` for `français`) beside the language's native name.

## Configuration (GUI)

On the menu bar, click `File -> Settings` and change the language using the drop-down menu.
Once the settings are closed, the manga currently being displayed will be reloaded to show the selected language.

## Todo

- [x] tests and docs (docs done)
- [x] create GUI to make downloading easier, like youtube-DLG
- [x] Add user configuration to select another language
- [ ] `Searcher` class (to search for manga?)
- [ ] i18n for selected language?

## Install

`pip install tankobon`

## Contributing

Just send in a PR with your feature changes/bug fixes. To set up development builds for tankobon, do the following:

```bash
$ git clone https://github.com/ongyx/tankobon && cd tankobon

# (create and enter a virtualenv if you want)
$ flit install -s  # Install tankobon as a symlink (any changes to source code will be reflected immediately)

# (make your code changes here...)

# make sure all tests pass
$ pytest
```

## Credits

[feather](https://github.com/feathericons/feather) for the icons (all svgs) in the [`resources`](./resources) folder.

## License

MIT.
