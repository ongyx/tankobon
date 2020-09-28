# manhua
> 漫画: (literal: slow drawing), a comic.

![logo](https://raw.githubusercontent.com/ongyx/manhua/master/logo.png "manhua")

## What?
manhua is a website scraper specifically geared towards downloading pictures from websites, i.e comics/mangas.

manhua is based around __bootstraps__, which are normal Python scripts that defines how to extract the image links from a webpage.
These links are outputted in a standardised format as JSON (see the `manhua/schema.py` file), called the __index__.
__Bootstrap__ scripts are stored in `bootstraps/`, and __index__ files are stored in `bootstraps/INDEX.zip`.

Bootstrap names should be a valid Python identifier. (This is important!)

## Depends
- `python` - At least version 3.6.
- `requests` - Downloader.
- `bs4` - Powerful HTML parser.


## Install
`python(3) -m pip install manhua`

## License
MIT.
