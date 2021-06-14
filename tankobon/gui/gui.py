# coding: utf8
"""
# tankobon, version {version}

Copyright (c) 2020-2021 Ong Yong Xin

Licensed under the MIT License.

star this project at [ongyx/tankobon](https://github.com/ongyx/tankobon) or something, idk

sources:

{supported}
"""

import pathlib
import signal
import sys
import threading
import traceback

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
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
    QSplashScreen,
    QTextBrowser,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
)

from .. import core, models, sources  # noqa: F401
from ..utils import Config
from . import resources, template, utils  # noqa: F401

from ..__version__ import __version__

_app = QApplication([])
QStyle = _app.style()

LOGO = QPixmap(":/logo.jpg")

HOME = pathlib.Path.home()

CONFIG = Config()
LANG = CONFIG["lang"]

CACHE = core.Cache()

MAX_COL = 5

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


class AboutBox(MessageBox):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("About")

        # build table of supported sources
        supported = []
        for cls in core.Parser.registered:
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

        cover = QPixmap()
        try:
            manga_path = CACHE.root / meta.hash
            cover_path = next(manga_path.glob("cover.*"))

        except StopIteration:
            cover = QPixmap(":/missing.jpg")

        else:
            cover.load(str(cover_path))

        # scale cover
        self.cover = cover.scaled(
            self.width(),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.cover_label = QLabel()
        self.cover_label.setPixmap(self.cover)
        self.resizeCover()
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
        layout.addWidget(source, 6, 1)

    def resizeCover(self):
        self.cover = self.cover.scaled(
            int(self.width() / 2),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.cover_label.setPixmap(self.cover)


# A list of manga items in the sidebar.
class ItemList(QListWidget):
    def __init__(self):
        super().__init__()
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


# Toolbar at the bottom of the window.
# This shows a bunch of buttons to manage manga items (add, remove, etc.)
class ToolBar(QToolBar):

    deletedManga = Signal()

    BUTTONS = [
        ("add", ":/plus.svg"),
        (
            "delete",
            ":/minus.svg",
        ),
        (
            "refresh",
            ":/refresh-cw.svg",
        ),
        (
            "download",
            ":/download.svg",
        ),
        ("view", ":/eye.svg"),
        ("locate", ":/folder.svg"),
    ]

    def __init__(self):
        super().__init__()
        MANGA_ITEMS.itemClicked.connect(self.onSelectedManga)
        self.deletedManga.connect(self.onDeletedManga)

        self.selected = None

        self.summaries = {}

        bg_is_dark = utils.is_dark(_app.palette().window().color())

        for method_name, icon_path in self.BUTTONS:

            method = getattr(self, method_name)
            tooltip = f"{method_name.title()} a manga..."

            if bg_is_dark:
                icon = QIcon(icon_path.replace(".svg", "-light.svg"))
            else:
                icon = QIcon(icon_path)

            action = QAction()
            action.setToolTip(tooltip)
            action.setIcon(icon)
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
            parser = core.Parser.parser(manga.meta.url)
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
            parser = core.Parser.parser(url)
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

    def _download(self, manga, chapters):
        dialog = ProgressDialog(self)

        parser = core.Parser.parser(manga.meta.url)

        with core.Downloader(CACHE.root / manga.meta.hash) as downloader:
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

        chapters = manga.select(dialog.textValue(), lang=LANG)
        if not chapters:
            MessageBox.warn(T_DOWNLOAD, "Chapters/range is invalid.")

        self._download(manga, chapters)

    def view(self):
        if not self.ensureSelected("view"):
            return

        MessageBox.info("oops", "Sorry! The viewer isn't implemented yet.")

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

    def about(self):
        about_box = AboutBox(self)
        about_box.exec()


# The combined manga item list plus preview.
class View(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)

        self.pixmap_cache = {}

        # The split view at first shows the list of manga items and the default item view.
        # After a manga has been selected, there will be a total of three widgets:
        # - Manga item list
        # - Manga info.
        # - Manga cover
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

        manga = _load_manga(manga_item.meta.hash)

        text = QTextBrowser()
        text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text.setReadOnly(True)
        text.setOpenExternalLinks(True)
        text.document().setDefaultStyleSheet(
            utils.resource(":/view.css").decode("utf8")
        )
        text.setHtml(template.create(manga))

        self.layout.addWidget(text)

        infobox = ItemInfoBox(manga_item)
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.verticalScrollBar().setStyleSheet("height:0px;")
        scroll.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        scroll.setWidget(infobox)

        self.layout.addWidget(scroll)

    def onDeletedManga(self):
        self.deleteLast()

        self.layout.addWidget(self.default())


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

    def confirmQuit(self):
        reply = MessageBox.ask(
            "Quit?",
            "Are you sure you want to exit?",
        )
        return reply == MessageBox.Yes

    def closeEvent(self, event):
        if self.confirmQuit():

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
