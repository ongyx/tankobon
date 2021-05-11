# coding: utf8

import pathlib
import signal
import sys
import traceback

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QMenuBar,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QSplashScreen,
    QSplitter,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import core, parsers, resources  # noqa: F401
from .__version__ import __version__

_app = QApplication([])
QStyle = _app.style()

LOGO = resources.pixmap("logo")

HOME = pathlib.Path.home()
CACHE = core.Cache()

MAX_COL = 5

T_CREATE = "Create Manga"
T_DELETE = "Delete Manga"


def delete(widget):
    widget.hide()
    widget.deleteLater()


class SpinningCursor:
    def __enter__(self):
        _app.setOverrideCursor(Qt.WaitCursor)

    def __exit__(self, t, v, tb):
        _app.restoreOverrideCursor()


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


# A manga item.
class Item(QListWidgetItem):
    def __init__(self, metadata: dict):
        self.meta = core.Metadata(**metadata)
        super().__init__(self.meta.title)

        self.setToolTip(", ".join(self.meta.alt_titles))


# A preview of the manga infomation (title, author, etc.)
class ItemView(QWidget):
    def __init__(self, item: Item):
        super().__init__()
        self.item = item

        self.layout = QHBoxLayout(self)

        self.cover = QPixmap()

        # load cover
        try:
            cover_path = next(CACHE._hash_path(self.item.meta.url).glob("cover.*"))

        except StopIteration:
            self.cover = resources.pixmap("missing")

        else:
            self.cover.load(str(cover_path))

        self.label = QLabel()
        self.resizeCover()

        self.layout.addWidget(self.label)

        desc = QLabel(self.item.meta.desc)
        desc.setWordWrap(True)

        self.layout.addWidget(desc)

    def resizeCover(self):
        self.cover = self.cover.scaled(
            int(self.width() / 2),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.label.setPixmap(self.cover)


# A list of manga items in the sidebar.
class ItemList(QListWidget):
    def __init__(self):
        super().__init__()

        for _, metadata in CACHE.index.items():
            self.addItem(Item(metadata))

        self.reload()

    def reload(self):
        self.setMaximumWidth(self.sizeHintForColumn(0) + 5)

    def onAddItem(self, item):
        self.addItem(item)
        self.limitSize()


MANGA_ITEMS = ItemList()


class ChaptersView(QScrollArea):
    def __init__(self, manga: core.Manga):
        super().__init__()
        self.manga = manga

        self.container = QWidget()
        self.setWidget(self.container)

        self.layout = QVBoxLayout(self.container)

        for cid in self.manga.data.keys():
            checkbox = QCheckBox(cid)
            self.layout.addWidget(checkbox)


# Toolbar at the bottom of the window.
# This shows a bunch of buttons to manage manga items (add, remove, etc.)
class ToolBar(QToolBar):

    deletedManga = Signal()

    BUTTONS = [
        {
            "method": "create",
            "tooltip": "Add a manga...",
            "icon": QStyle.SP_FileDialogNewFolder,
        },
        {
            "method": "delete",
            "tooltip": "Delete the selected manga...",
            "icon": QStyle.SP_TrashIcon,
        },
        {
            "method": "refresh",
            "tooltip": "Refresh the selected manga...",
            "icon": QStyle.SP_BrowserReload,
        },
        {
            "method": "download",
            "tooltip": "Download the selected manga...",
            "icon": QStyle.SP_DialogSaveButton,
        },
    ]

    def __init__(self):
        super().__init__()
        MANGA_ITEMS.itemClicked.connect(self.onSelectedManga)
        self.deletedManga.connect(self.onDeletedManga)

        self.selected = None

        self.summaries = {}

        for button_info in self.BUTTONS:
            method = getattr(self, button_info["method"])
            tooltip = button_info["tooltip"]
            icon = QStyle.standardIcon(button_info["icon"])

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

        url = manga_item.meta.url
        if url not in self.summaries:
            manga = CACHE.load(url)
            self.summaries[url] = f"{len(manga.data)} chapters, {manga.total()} pages"

        self.summary.setText(self.summaries[url])

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

    def create(self):
        dialog = RequiredDialog()
        dialog.setWindowTitle(T_CREATE)
        dialog.setLabelText("Enter the manga url below:")

        dialog_code = dialog.exec()
        if dialog_code == QInputDialog.Rejected:
            # canceled
            return

        url = dialog.textValue()

        if url in CACHE.index:
            MessageBox.info(
                T_CREATE,
                "Manga already exists in cache. To refresh a manga, select a manga and click the refresh button.",
            )
            return

        try:
            manga = core.Manga.from_url(url)
        except core.UnknownDomainError:
            MessageBox.warn(
                T_CREATE,
                "Manga url is invalid or no parser was found for the url.",
            )
            return

        with SpinningCursor():
            manga.refresh(pages=True)
            CACHE.save(manga, cover=True)

        # add to item list
        MANGA_ITEMS.addItem(Item(manga.meta.__dict__))
        MANGA_ITEMS.reload()
        QApplication.processEvents()

    def delete(self):
        if not self.ensureSelected("delete"):
            return

        reply = MessageBox.ask(
            T_DELETE,
            "Are you sure you want to delete this manga? This cannot be undone!",
        )

        if reply == MessageBox.Yes:
            CACHE.delete(self.selected.meta.url)
            MANGA_ITEMS.takeItem(MANGA_ITEMS.row(self.selected))
            MANGA_ITEMS.reload()

            self.deletedManga.emit()

    def refresh(self):
        if not self.ensureSelected("refresh"):
            return

        with SpinningCursor():
            manga = CACHE.load(self.selected.meta.url)
            manga.refresh(pages=True)
            CACHE.save(manga)

    def download(self):
        """
        if not self.ensureSelected("download"):
            return

        manga = CACHE.load(self.selected.meta.url)

        # ask which chapters to download
        chapters_view = ChaptersView(manga)
        chapters_view.show()

        download_path = QFileDialog.getExistingDirectory(
            self, "Choose a folder to download to.", str(HOME)
        )
        """


# Toolbar at the top of the window.
class MenuBar(QMenuBar):
    def __init__(self):
        super().__init__()

        file_menu = self.addMenu("File")

        file_quit = QAction("Quit", self)
        file_quit.triggered.connect(_app.quit)

        file_menu.addAction(file_quit)


# The combined manga item list plus preview.
class View(QSplitter):
    def __init__(self):
        super().__init__()

        # cache pixmaps so we don't have to keep loading them.
        self.pixmap_cache = {}

        # The split view at first shows the list of manga items and the default item view.
        # After a manga has been selected, there will be a total of three widgets:
        # - Manga item list
        # - Manga cover
        # - Manga info.
        self.addWidget(MANGA_ITEMS)
        self.addWidget(self.default())

        MANGA_ITEMS.itemClicked.connect(self.onSelectedManga)

    def default(self):
        label = QLabel("Select a manga from the side bar, or add a new one.")
        label.setAlignment(Qt.AlignCenter)

        return label

    def deleteLast(self):
        delete(self.widget(self.count() - 1))

    def onSelectedManga(self, manga_item):
        self.deleteLast()

        item_view = ItemView(manga_item)
        self.addWidget(item_view)

    def onDeletedManga(self):
        self.deleteLast()

        self.addWidget(self.default())


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


if __name__ == "__main__":

    splash = LoadingSplash(LOGO)
    splash.show()

    splash.showMessage("Loading manga metadata...")

    window = Root()

    window.show()
    splash.finish(window)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(_app.exec_())
