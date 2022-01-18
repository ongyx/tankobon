# coding: utf8
"""
# tankobon {version}

Copyright (c) 2020-2021 Ong Yong Xin

Licensed under the MIT License.

star this project at [ongyx/tankobon](https://github.com/ongyx/tankobon) or something, idk

sources:

{supported}
"""

import functools
import pathlib
import signal
import sys
import threading
import traceback

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QMenuBar,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressDialog,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplashScreen,
    QTabWidget,
    QTableWidget,
    # QTableWidgetItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
)

import natsort  # type: ignore

from .. import core, iso639, models
from ..sources.base import Parser
from ..utils import CONFIG

from ..__version__ import __version__

from . import common, resources, template, utils

_app = QApplication([])
_app.setAttribute(Qt.AA_UseHighDpiPixmaps)

QStyle = _app.style()

LOGO = QPixmap(":/logo.jpg")

HOME = pathlib.Path.home()

CACHE = core.Cache()

T_ADD = "Add Manga"
T_DELETE = "Delete Manga"
T_DOWNLOAD = "Download Manga"

MANGA = {}
MANGA_LOCK = threading.Lock()


def _is_ascii(s):
    try:
        s.encode(encoding="utf8").decode("ascii")
    except UnicodeDecodeError:
        return False
    else:
        return True


def _normalize(s):
    return s.replace("_", " ").capitalize()


def _load_manga(hash):
    with MANGA_LOCK:
        if hash not in MANGA:
            MANGA[hash] = CACHE.load(hash)

        return MANGA[hash]


def delete(widget):

    if isinstance(widget, QWidgetItem):
        widget.widget().close()

    else:
        widget.hide()
        widget.deleteLater()


class SpinningCursor:
    def __enter__(self):
        _app.setOverrideCursor(Qt.WaitCursor)

    def __exit__(self, t, v, tb):
        _app.restoreOverrideCursor()


class TitleLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)
        self.setTextFormat(Qt.RichText)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setStyleSheet("background-color: #CCCCFF; color: black;")
        self.setAutoFillBackground(True)


class SubtitleLabel(QLabel):
    def __init__(self, subtitle):
        super().__init__(f"<b>{subtitle}</b>")
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)


# A message box without the window icon.
class MessageBox(QMessageBox):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowIcon(QIcon(LOGO))

    @classmethod
    def info(cls, title, text):
        msgbox = cls(cls.Information, title, text, cls.Ok)
        return msgbox.exec()

    @classmethod
    def ask(cls, title, text):
        msgbox = cls(cls.Question, title, text, cls.Yes | cls.No)
        return msgbox.exec()

    @classmethod
    def warn(cls, title, text):
        msgbox = cls(cls.Warning, title, text, cls.Ok)
        return msgbox.exec()

    @classmethod
    def crit(cls, title, text):
        msgbox = cls(cls.Critical, title, text, cls.Ok)
        return msgbox.exec()


def _excepthook(ex_type, ex_value, ex_traceback):
    MessageBox.crit(
        "An exception occured.",
        "".join(traceback.format_exception(ex_type, ex_value, ex_traceback)),
    )


sys.excepthook = _excepthook


# A text dialog that requires input before allowing 'ok' to be pressed.
class RequiredDialog(QInputDialog):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowIcon(QIcon(LOGO))

        self.textValueChanged.connect(self.onTextValueChanged)

        self.setInputMode(self.TextInput)

        self.setOkButtonText("Ok")

        self.ok_button, _ = self.findChild(QDialogButtonBox).buttons()
        self.ok_button.setEnabled(False)

    def onTextValueChanged(self, text):
        if text:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)


class ProgressDialog(QProgressDialog):
    def __init__(self, *args):
        super().__init__(*args)

        self.setMinimumDuration(0)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_DeleteOnClose, True)


class LanguageComboBox(QComboBox):
    def __init__(self):
        super().__init__()

        index = None

        for code, lang in iso639.DATASET.items():
            self.addItem(f"{lang.native_name} ({code})", code)
            if code == CONFIG["lang"]:
                index = self.count() - 1

        self.setCurrentIndex(index)

        self.currentIndexChanged.connect(self.onCurrentIndexChanged)

    def onCurrentIndexChanged(self, index):
        CONFIG["lang"] = self.currentData()


class RateLimitSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setMinimum(1)
        self.setValue(CONFIG["download.rate_limit"])
        self.valueChanged.connect(self.onValueChanged)

    def onValueChanged(self, value):
        CONFIG["download.rate_limit"] = value


class DataSaverCheckBox(QCheckBox):
    def __init__(self):
        super().__init__("Data saver (low-quality pages)")

        state = Qt.Unchecked
        if CONFIG["mangadex.data_saver"]:
            state = Qt.Checked

        self.setCheckState(state)
        self.stateChanged.connect(self.onStateChanged)

    def onStateChanged(self, state):
        CONFIG["mangadex.data_saver"] = state == Qt.Checked


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)


class Settings(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self.general(), "General")
        tabs.addTab(self.downloads(), "Downloads")
        tabs.addTab(self.sources(), "Sources")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def general(self):
        tab = SettingsTab()

        tab.layout.addWidget(QLabel("Language"))
        tab.layout.addWidget(LanguageComboBox())

        return tab

    def downloads(self):
        tab = SettingsTab()

        tab.layout.addWidget(QLabel("Rate Limit"))

        spinbox = RateLimitSpinBox()
        spinbox.setToolTip(
            (
                "The maximum number of requests that can be made concurrently.\n"
                "Lower values reduce bandwidth usage but downloads will be slower."
            )
        )
        tab.layout.addWidget(spinbox)

        return tab

    def sources(self):
        tab = SettingsTab()

        tab.layout.addWidget(QLabel("Mangadex"))

        data_saver = DataSaverCheckBox()
        data_saver.setToolTip(
            "Download low-quality pages to save bandwidth and disk space."
        )
        tab.layout.addWidget(data_saver)

        return tab


class AboutBox(MessageBox):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("About")

        # build table of supported sources
        supported = []
        for cls in Parser.registered:
            supported.append(f"`{cls.__module__}` ({cls.domain.pattern})  ")

        self.setTextFormat(Qt.MarkdownText)
        self.setText(
            __doc__.format(
                version=__version__,
                supported="\n".join(supported),
            )
        )

        self.setAttribute(Qt.WA_DeleteOnClose)

        small_logo = LOGO.scaled(
            QSize(256, 256), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.setIconPixmap(small_logo)


# A manga item.
class Item(QListWidgetItem):
    def __init__(self, meta: models.Metadata):
        self.meta = meta
        super().__init__(self.meta.title)

        # self.setToolTip(", ".join(self.meta.alt_titles))


# A preview of the manga infomation (title, author, etc.)
class ItemInfoBox(QWidget):
    def __init__(self, item: Item):
        super().__init__()
        layout = QGridLayout(self)

        meta = item.meta

        # infobox spans one row and two columns.
        SPAN = (1, 2)

        # wikipedia-style info box at the side
        title = TitleLabel(f"<h2><i>{meta.title}</i></h2>")
        layout.addWidget(title, 0, 0, *SPAN)

        self.cover = QPixmap()

        try:
            manga_path = CACHE.root / meta.hash
            cover_path = next(manga_path.glob("cover.*"))

        except StopIteration:
            self.cover.load(":/missing.jpg")

        else:
            self.cover.load(str(cover_path))

        self.cover = self.cover.scaled(
            int(self.width() / 2),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.cover_label = QLabel()
        self.cover_label.setScaledContents(True)
        self.cover_label.setPixmap(self.cover)

        layout.addWidget(self.cover_label, 1, 0, *SPAN)

        if meta.alt_titles is not None:
            _alt_titles = "<br>".join(
                f"<i>{t}</i>" if _is_ascii(t) else t for t in meta.alt_titles
            )

        else:
            _alt_titles = "(empty)"

        alt_titles = TitleLabel(_alt_titles)
        alt_titles.setStyleSheet("background-color: #DDDDFF; color: black;")
        layout.addWidget(alt_titles, 2, 0, *SPAN)

        genre_header = SubtitleLabel("Genre")
        layout.addWidget(genre_header, 3, 0)

        if meta.genres is not None:
            _genres = "<br>".join(_normalize(g) for g in meta.genres)

        else:
            _genres = "(empty)"

        genres = QLabel(_genres)
        layout.addWidget(genres, 3, 1)

        manga_header = TitleLabel("<b>Manga</b>")
        layout.addWidget(manga_header, 4, 0, *SPAN)

        author_header = SubtitleLabel("Authored by")
        layout.addWidget(author_header, 5, 0)

        if meta.authors is not None:
            _authors = "<br>".join(a for a in meta.authors)

        else:
            _authors = "(empty)"

        authors = QLabel(_authors)
        layout.addWidget(authors, 5, 1)

        source_header = SubtitleLabel("Source")
        layout.addWidget(source_header, 6, 0)

        source = QLabel(f'<a href="{meta.url}">{meta.url}</b>')
        source.setWordWrap(True)
        source.setOpenExternalLinks(True)
        layout.addWidget(source, 6, 1)

        langs_header = SubtitleLabel("Languages")
        layout.addWidget(langs_header, 7, 0)

        manga = CACHE[meta.hash]
        langs_set = set()

        for chapter in manga["chapters"].values():
            langs_set.update(chapter.keys())

        langs = QLabel("<br>".join(common.describe_langs(list(langs_set))))
        layout.addWidget(langs, 7, 1)


# A list of manga items in the sidebar.
class ItemList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)

        self.hashs = set()

        for _, manga in CACHE.data.items():
            self.addItem(Item(manga["meta"]))

        self.reload()

    def addItem(self, item):
        self.hashs.add(item.meta.hash)
        super().addItem(item)

    def reload(self):
        self.setMaximumWidth(self.sizeHintForColumn(0) + 5)


MANGA_ITEMS = ItemList()


class PageViewToolBar(QToolBar):

    BUTTONS = [
        ("start", "chevrons-left"),
        ("previous", "chevron-left"),
        ("pageno", ""),
        ("next", "chevron-right"),
        ("end", "chevrons-right"),
    ]

    setPage = Signal(int)

    def __init__(self, total):

        super().__init__()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: red")
        self.setMovable(True)
        self.setFloatable(True)

        self.pageno = 1
        self.total = total
        self.label = QLabel()

        self.setPage.connect(self.onSetPage)

        for method_name, icon_path in self.BUTTONS:

            if method_name == "pageno":
                self.addWidget(self.label)
                continue

            method = getattr(self, method_name)
            tooltip = f"{method_name.title()} page..."

            icon = utils.icon(icon_path)

            action = self.addAction(icon, tooltip)
            action.triggered.connect(method)

    def onSetPage(self, pageno):
        self.pageno = pageno
        self.label.setText(f"{pageno} / {self.total}")

        actions = self.actions()
        for action in actions:
            action.setEnabled(True)

        # disable start/prev or end/next actions on the first and last page respectively.
        disable = []

        if self.pageno == 1:
            disable = actions[:2]
        elif self.pageno == self.total:
            disable = actions[2:]

        for action in disable:
            action.setEnabled(False)

    def start(self):
        self.setPage.emit(1)

    def previous(self):
        self.setPage.emit(self.pageno - 1)

    def next(self):
        self.setPage.emit(self.pageno + 1)

    def end(self):
        self.setPage.emit(self.total)


class PageView(QScrollArea):
    def __init__(self, parent, pages):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setStyleSheet("background-color: #000000")
        self.setWidgetResizable(True)

        self.pages = pages

        self.label = QLabel()
        self.label.setScaledContents(True)

        self.setWidget(self.label)

        self.toolbar = PageViewToolBar(len(self.pages))
        self.toolbar.setPage.connect(self.onSetPage)

        self._height = self.label.height() + self.toolbar.height() / 2

        self.toolbar.start()

    def onSetPage(self, pageno):
        pixmap = QPixmap(self.pages[pageno - 1])

        self.label.setPixmap(pixmap)


def _download(manga, chapters, downloader):
    dialog = ProgressDialog()

    parser = Parser.by_url(manga.meta.url)

    for count, chapter in enumerate(chapters):

        dialog.setLabelText(f"Downloading chapter {chapter.id}...")

        if not chapter.pages:
            parser.add_pages(chapter)

        total = len(chapter.pages)

        # HACK: make the progress bar display properly during first iteration
        dialog.setMaximum(total)
        dialog.setValue(total - 1)
        dialog.setValue(0)

        if dialog.wasCanceled():
            break

        downloader.download(chapter, progress=dialog.setValue)

        dialog.setValue(total)


# Toolbar at the bottom of the window.
# This shows a bunch of buttons to manage manga items (add, remove, etc.)
class ToolBar(QToolBar):

    deletedManga = Signal()

    BUTTONS = [
        ("add", "plus"),
        (
            "delete",
            "minus",
        ),
        (
            "refresh",
            "refresh-cw",
        ),
        # ("download", "download",),
        ("locate", "folder"),
    ]

    def __init__(self):
        super().__init__()
        MANGA_ITEMS.itemClicked.connect(self.onSelectedManga)
        self.deletedManga.connect(self.onDeletedManga)

        self.selected = None

        self.summaries = {}

        for method_name, icon_path in self.BUTTONS:

            method = getattr(self, method_name)
            tooltip = f"{method_name.title()} a manga..."

            action = QAction()
            action.setToolTip(tooltip)
            action.setIcon(utils.icon(icon_path))
            action.triggered.connect(method)

            button = QToolButton()
            button.setDefaultAction(action)

            self.addWidget(button)

        # spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        # text below the manga preview
        self.summary = QLabel()
        self.addWidget(self.summary)

        self.show()

    def onSelectedManga(self, manga_item):
        self.selected = manga_item

        hash = manga_item.meta.hash
        if hash not in self.summaries:
            manga = _load_manga(hash)
            self.summaries[hash] = f"{len(manga.chapters)} chapters"

        self.summary.setText(self.summaries[hash])

    def onDeletedManga(self):
        self.summary.setText("")

    def ensureSelected(self, method):
        if self.selected is None:
            MessageBox.info(
                f"{method.capitalize()} Manga",
                f"Please select a manga to {method} first.",
            )
            return False

        return True

    def _refresh(self, manga):

        with SpinningCursor():
            parser = Parser.by_url(manga.meta.url)
            parser.add_chapters(manga)

            CACHE.dump(manga)

            # add to item list (only if manga is new)
            if manga.meta.hash not in MANGA_ITEMS.hashs:
                MANGA_ITEMS.addItem(Item(manga.meta))
                MANGA_ITEMS.reload()

    def add(self):
        dialog = RequiredDialog()
        dialog.setWindowTitle(T_ADD)
        dialog.setLabelText("Enter the manga url below:")

        dialog_code = dialog.exec()
        if dialog_code == QInputDialog.Rejected:
            # canceled
            return

        url = dialog.textValue()

        if url in CACHE.alias:
            MessageBox.info(
                T_ADD,
                "Manga already exists in cache. To refresh a manga, select a manga and click the refresh button.",
            )
            return

        try:
            parser = Parser.by_url(url)
        except core.UnknownDomainError:
            MessageBox.warn(
                T_ADD,
                "Manga url is invalid or no parser was found for the url.",
            )
            return

        manga = parser.create(url)

        self._refresh(manga)

        if manga.meta.cover:
            with core.Downloader(CACHE.root / manga.meta.hash) as downloader:
                downloader.download_cover(manga)

    def delete(self):
        if not self.ensureSelected("delete"):
            return

        reply = MessageBox.ask(
            T_DELETE,
            "Are you sure you want to delete this manga? This cannot be undone!",
        )

        if reply == MessageBox.Yes:
            CACHE.delete(self.selected.meta.hash)
            MANGA_ITEMS.takeItem(MANGA_ITEMS.row(self.selected))
            MANGA_ITEMS.reload()

            self.deletedManga.emit()

    def refresh(self):
        if not self.ensureSelected("refresh"):
            return

        manga = _load_manga(self.selected.meta.hash)
        self._refresh(manga)
        # reload view
        MANGA_ITEMS.itemClicked.emit(self.selected)

    def download(self):
        if not self.ensureSelected("download"):
            return

        manga = _load_manga(self.selected.meta.hash)

        dialog = RequiredDialog()
        dialog.setWindowTitle(T_DOWNLOAD)
        dialog.setLabelText(
            "Enter the chapters to download below, seperated by commas.\n"
            "Ranges are also allowed, i.e 1-5."
        )

        dialog_code = dialog.exec()
        if dialog_code == QInputDialog.Rejected:
            return

        chapters = manga.select(dialog.textValue(), lang=CONFIG["lang"])
        if not chapters:
            MessageBox.warn(T_DOWNLOAD, "Chapters/range is invalid.")

        with core.Downloader(CACHE.root / manga.meta.hash) as downloader:
            _download(manga, chapters, downloader)

    def locate(self):
        if not self.ensureSelected("locate"):
            return

        hash = self.selected.meta.hash

        utils.xopen(str(CACHE.root / hash))


# Toolbar at the top of the window.
class MenuBar(QMenuBar):
    def __init__(self):
        super().__init__()

        file = self.addMenu("File")

        file_settings = QAction("Settings", self)
        file_settings.triggered.connect(self.settings)
        file.addAction(file_settings)

        file_quit = QAction("Quit", self)
        file_quit.triggered.connect(_app.quit)
        file.addAction(file_quit)

        help = self.addMenu("Help")

        help_tankobon = QAction("About tankobon", self)
        help_tankobon.triggered.connect(self.about)
        help.addAction(help_tankobon)

        help_qt = QAction("About Qt", self)
        help_qt.triggered.connect(_app.aboutQt)
        help.addAction(help_qt)

    def settings(self):
        settings_dialog = Settings(self)
        settings_dialog.exec()
        self.parentWidget().reload()

    def about(self):
        about_box = AboutBox(self)
        about_box.exec()


# A grid of manga chapters.
class ChapterView(QTableWidget):
    def __init__(self, manga):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

        self.buttons = {}

        self.manga = manga
        self.downloader = core.Downloader(CACHE.root / self.manga.meta.hash)

        chapters = natsort.natsorted(
            [
                chapter
                for chapter, langs in manga.chapters.items()
                if CONFIG["lang"] in langs
            ]
        )

        self.setRowCount(len(chapters))
        self.setColumnCount(4)

        self.setHorizontalHeaderLabels(["status", "volume", "chapter", "title"])

        for row, chapter in enumerate(chapters):
            self.addChapter(row, manga.chapters[chapter][CONFIG["lang"]])

    def addChapter(self, row, chapter):

        if self.downloader.downloaded(chapter):
            icon = utils.icon("eye")
        else:
            icon = utils.icon("download")

        button = QToolButton()
        button.setStyleSheet("border: none;")
        button.setIcon(icon)
        button.clicked.connect(functools.partial(self.onClicked, chapter))
        self.buttons[chapter.id] = button
        self.setCellWidget(row, 0, button)

        volume = QLabel(chapter.volume or "(empty)")
        volume.setAlignment(Qt.AlignCenter)
        self.setCellWidget(row, 1, volume)

        id = QLabel(chapter.id)
        id.setAlignment(Qt.AlignCenter)
        self.setCellWidget(row, 2, id)

        title = QLabel(f'<a href="{chapter.url}">{chapter.title or "(empty)"}</a>')
        title.setOpenExternalLinks(True)
        self.setCellWidget(row, 3, title)

    def onClicked(self, chapter):
        if not self.downloader.downloaded(chapter):
            _download(self.manga, [chapter], self.downloader)
            self.downloader.manifest.sync()

        self.buttons[chapter.id].setIcon(utils.icon("eye"))

        # pages = self.downloader.manifest[chapter.id][chapter.lang]
        # page_view = PageView(self, pages)
        # page_view.showMaximized()

        utils.xopen(str(self.downloader.path / chapter.id / chapter.lang))


# The manga chapters plus description.
class SummaryView(QWidget):
    def __init__(self, manga):
        super().__init__()

        self.layout = QVBoxLayout(self)

        chapters = ChapterView(manga)

        self.layout.addWidget(chapters)

        desc = QLabel()
        desc.setTextInteractionFlags(Qt.TextBrowserInteraction)
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.RichText)
        desc.setOpenExternalLinks(True)
        desc.setText(template.create(manga, lang=CONFIG["lang"]))

        self.layout.addWidget(desc)


# The combined manga item list plus preview.
class View(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)

        self.selected = None
        self.pixmap_cache = {}

        # The split view at first shows the list of manga items and the default item view.
        # After a manga has been selected, there will be a total of three widgets:
        # - Manga item list
        # - Manga description
        # - Manga info (incl. cover)
        self.layout.addWidget(MANGA_ITEMS)
        self.layout.addWidget(self.default())

        MANGA_ITEMS.itemClicked.connect(self.onSelectedManga)

    def default(self):
        label = QLabel("Select a manga from the side bar, or add a new one.")
        label.setAlignment(Qt.AlignCenter)

        return label

    def deleteLast(self):
        while self.layout.count() != 1:
            delete(self.layout.takeAt(1))

    def onSelectedManga(self, manga_item):
        self.deleteLast()
        self.selected = manga_item

        manga = _load_manga(manga_item.meta.hash)

        summary = SummaryView(manga)

        self.layout.addWidget(summary)

        infobox = ItemInfoBox(manga_item)
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(scroll.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        scroll.setWidget(infobox)

        self.layout.addWidget(scroll)

    def onDeletedManga(self):
        self.deleteLast()

        self.layout.addWidget(self.default())

    def reload(self):
        if self.selected is not None:
            self.onSelectedManga(self.selected)

        else:
            # no manga selected yet.
            self.onDeletedManga()


# Main window.
class Root(QMainWindow):
    def __init__(self):
        super().__init__()

        # gui setup
        self.setWindowTitle("tankobon")
        self.setWindowIcon(LOGO)

        # can't direcly apply layouts to the main window, so wrap in a widget.
        wrapper = QWidget(self)
        self.layout = QVBoxLayout(wrapper)

        self.menubar = MenuBar()
        self.setMenuBar(self.menubar)

        self.view = View()
        self.layout.addWidget(self.view)

        self.toolbar = ToolBar()
        self.layout.addWidget(self.toolbar)

        self.toolbar.deletedManga.connect(self.view.onDeletedManga)

        self.setCentralWidget(wrapper)

    def reload(self):
        self.view.reload()

    def confirmQuit(self):
        reply = MessageBox.ask(
            "Quit?",
            "Are you sure you want to exit?",
        )
        return reply == MessageBox.Yes

    def closeEvent(self, event):
        if self.confirmQuit():
            CONFIG.close()
            CACHE.close()
            event.accept()
        else:
            event.ignore()


class LoadingSplash(QSplashScreen):
    def showMessage(self, message):
        super().showMessage(
            f"\ntankobon v{__version__}\nCopyright (c) 2020-2021 Ong Yong Xin\n{message}",
            Qt.AlignBottom,
            Qt.white,
        )


def main():
    splash = LoadingSplash(LOGO)
    splash.show()

    splash.showMessage("Loading manga metadata...")

    window = Root()

    window.show()
    splash.finish(window)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(_app.exec_())
