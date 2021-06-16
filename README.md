# tankobon

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/resources/logo.jpg "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)
![calver](https://img.shields.io/badge/calver-YY.MM.MICRO-22bfda.svg)

## What?

tankobon is (somewhat) like youtube-dl for manga websites: you can fetch manga from a few sources (websites).

Currently, the following websites are supported:

- `catmanga.org`
- `mangakakalot.com`
- `mangadex.org`

## Versioning Change

tankobon will now use the version format `YYYY.MM.MICRO`:

- `YYYY` is the full 4-digit year.
- `MM` is the 1-2 digit month.
- `MICRO` is the release number for that month.

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

## Note on mangadex

Since mangadex's frontend isn't really done yet, manga hosted there do not have a 'public' url yet.
To add a mangadex manga, the url must look like this:

```
https://mangadex.org/(manga uuid)
```

## Todo

- [x] tests and docs (docs done)
- [x] create GUI to make downloading easier, like youtube-DLG
- [ ] Add user configuration to select another language
- [ ] `Searcher` class (to search for manga?)

## Install

`pip install tankobon`

## Contributing

Just send in a PR with your feature changes/bug fixes. To set up development builds for tankobon, do the following:

```bash
$ git clone https://github.com/ongyx/tankobon && cd tankobon

# (create and enter a virtualenv if you want)
$ flit install -s  # Install tankobon as a symlink (any changes to source code will be reflected immediately)

# (make your code changes here...)

# Make sure to fix any style/type errors if they show up by running this.
$ pytest --flake8 --mypy
```

## Credits

[feather](https://github.com/feathericons/feather) for the icons (all svgs) in the [`resources`](./resources) folder.

## License

MIT.
