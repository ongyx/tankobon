# tankobon

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/logo.jpg "tankobon")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tankobon)](https://pypi.org/project/tankobon)
![PyPI - License](https://img.shields.io/pypi/l/tankobon)
![PyPI](https://img.shields.io/pypi/v/tankobon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tankobon)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/tankobon)

## What?
tankobon is a website scraper specifically geared towards downloading pictures from websites, i.e comics/mangas.

tankobon is based around __bootstraps__, which are normal Python scripts that defines how to extract the image links from a webpage.
These links are outputted in a standardised format as JSON (see the `tankobon/schema.py` file), called the __index__.
__Bootstrap__ scripts are stored in `bootstraps/`, and __index__ files are stored in `bootstraps/INDEX.zip`.

Bootstrap names should be a valid Python identifier. (This is important!)

## Depends
- `python` - At least version 3.6.
- `requests` - Downloader.
- `bs4` - Powerful HTML parser.


## Install
`python(3) -m pip install tankobon`

## Build
All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
To build, do `flit build`.

## License
MIT.
