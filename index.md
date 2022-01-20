---
layout: default
---

tankobon is a manga downloader powered by web scraping.

Downloading manga from supported [sources](#sources) is as easy as pie:

```bash
$ tankobon add https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8
Sucessfully added 'https://mangadex.org/title/b49fd121-19bf-4344-a8e1-d1be7ca04e08/sekai-saikyou-no-assassin-isekai-kizoku-ni-tensei-suru'! It's shorthash is <ffd84019>.

$ tankobon download ffd84019

# optionally, pack it into a PDF for e-readers.
$ tankobon pdfify -o manga.pdf
```

## Features

* Add manga from a variety of sources, and periodically refresh them to get newer chapters
* Download chapters pages quickly and pack them into a PDF for portability
* Flexible configuration for tankobon's behavior and sources
* multilingual support (only supported by `mangadex` source right now)

## Quickstart

Install with `pip install tankobon`. tankobon can be used in one of three ways:

* cli (using the `tankobon` command)
* gui (requires the `gui` extra, install with `pip install tankobon[gui]`)
* programmatically (check out the [documentation](https://ongyx.github.io/tankobon/docs) for more info)

```bash
tankobon add <url>  # add a new manga
tankobon download <shothash>  # download a manga
tankobon list  # list all manga along with their shorthashes and urls
tankobon refresh <shorthash>  # refresh a manga (adds new chapters)
tankobon remove <shorthash>  # remove a manga
```

tankobon uses a unique shorthash to identify each manga, derived from it's url.

## Sources

tankobon currently supports the following websites:

* `mangakakalot.com`
* `mangadex.org`

Feel free to contribute a PR or open a feature request issue to add more sources.

## Multilingual Support

You can set your preferred language to download MangaDex chapters for.
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

As for the GUI, in the menu bar, click `File -> Settings` and change the language using the drop-down menu.
Once the settings are closed, the manga currently being displayed will be reloaded to show the selected language.
