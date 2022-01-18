# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

## 2021.1.18

* Internal code reorganization.
* Removed the `catmanga` and `genshin` sources. (R.I.P Black Cat Scanlations)
* Removed dependency on fake_useragent in favour of an internal module `imposter`, which does the same thing.

## 2021.7.11 (11 July)

### Added

* Genshin Impact manga source.

## 2021.6.8 (22 June)

### Added

* New config option `download.rate_limit`: this limits the total number of requests made when downloading chapters at any one time.
  This can also be set in the GUI settings.
* Nicer chapter view that can be directly clicked on to download/view chapters.
* Method `core.Downloader.downloaded(chapter)`: Check whether the pages for a `models.Chapter` has been downloaded.

### Changed

* `utils.Config` no longer implicitly creates a single instance.
  It is strongly recommended to access the global instance `utils.CONFIG` to avoid stale configurations being written back to disk.

## 2021.6.7 (22 June)

### Fixed

* [#26](#26): The CatManga source now parses manga descriptions properly.
  Implicit wrapping of `str` descriptions in `models.Metadata` to dictionaries caused descriptions to be nested.


## 2021.6.6 (20 June)

### Added

* (GUI) Support for BBCode in manga descriptions.
  Any BBCode will now render correctly as HTML in the manga view.
* Dependency on bbcode.
* `.sync()` method to `utils.Config` (save config changes).

### Changed

* (GUI) The visual layout has been changed a bit to prepare for viewer support.
* The `desc` field of `models.Metadata` is now a dictionary map of a language code to the localised description.

### Fixed

* Configuration was not synced across `utils.Config` instances (i.e language), so newer configs would get overwritten by older ones.
  `utils.Config` now will have only one instance to prevent this.
* (GUI) Cover images now scale correctly and no longer look pixelated, especially those of high resolution.

## 2021.6.5 (18 June)

### Added

* Settings dialog in the GUI (File -> Settings).
  The preferred manga language can now be set through there.
* The manga info panel now shows the languages in the manga.

### Changed

* Mangadex urls must now start with `mangadex.org/title`.

### Removed

* Dependency on dataclasses-json.

### Fixed

* The GUI now shows chapters for the current language set.
* The Mangadex source now adds all languages to the manga.
* Mangadex chapter urls will now open correctly when clicked in the GUI.
* Downloading through the CLI. `Parser.by_url` was given the shorthash instead of the url.

## 2021.6.4 (16 June)

### Changed

* All source-related abstract base classes (i.e `Parser`) now reside in `tankobon/sources/base.py`.
  The source modules have been updated accordingly to reflect this.
* The method `Parser.parser` has been renamed to `Parser.by_url` to make it clearer what it is actually for.

## 2021.6.3 (14 June)

### Changed

* The root manga index file (at `~/.local/share/tankobon/index.json`) is now compressed with GZip.
  This should have significant space savings on disk, especially for large indexes (with a lot of manga).

## 2021.6.2 (11 June)

### Changed

* The bottom GUI in the toolbar now shows the correct colour icons (white for a dark system theme, and vice versa).
* Added locate button in the toolbar.

## 2021.6.1 (5 June)

### Added

* Dependency on [MangaDex.py](https://github.com/Proxymiity/MangaDex.py).
* Progess bar and about box in the GUI.
* Mangadex source (not complete yet).

### Changed

* Versioning system is now based on date in the form of `YYYY.MM.patch`, where patch is the release number for that month.
* Renamed `tankobon.parsers` to `tankobon.sources`.

### Fixed

* Checks for None when presenting Metadata objects in the GUI.
  Previously, any None values would cause `TypeError`.
