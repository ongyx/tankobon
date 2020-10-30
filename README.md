# tankobon

![logo](https://raw.githubusercontent.com/ongyx/tankobon/master/logo.jpg "tankobon")

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
