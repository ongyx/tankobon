# coding: utf8

import signal
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QMessageBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplashScreen,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from . import core, parsers  # noqa: F401
from .__version__ import __version__

_app = QApplication([])

MAX_COL = 5
LOGO = QPixmap("logo.jpg")
NO_MANGA = QLabel("Select a manga from the side bar, or add a new one.")
NO_MANGA.setAlignment(Qt.AlignCenter)


class MangaItem(QListWidgetItem):
    def __init__(self, metadata: dict):
        self.meta = core.Metadata(**metadata)
        super().__init__(self.meta.title)

        self.setToolTip(", ".join(self.meta.alt_titles))


class MangaItemDisplay(QWidget):
    def __init__(self, metadata: dict):
        self.meta = core.Metadata(**metadata)
        super().__init__()

        self.layout = QGridLayout(self)


class Root(QMainWindow):
    def __init__(self):
        super().__init__()

        # gui setup
        self.setWindowTitle("tankobon")
        self.setWindowIcon(LOGO)

        file_menu = self.menuBar().addMenu("File")
        file_quit = QAction("Quit", self)
        file_quit.triggered.connect(_app.quit)
        file_menu.addAction(file_quit)

        manga_list = QListWidget()

        # actual tankobon api
        self.cache = core.Cache()

        for _, metadata in self.cache.index.items():
            manga_list.addItem(MangaItem(metadata))

        manga_list.itemClicked.connect(self.selectedManga)
        manga_list.setMaximumWidth(manga_list.sizeHintForColumn(0) + 5)

        self.manga_view = QSplitter()

        self.manga_view.addWidget(manga_list)
        self.manga_view.addWidget(NO_MANGA)

        self.manga_view.setCollapsible(0, False)

        wrapper = QWidget(self)
        self.layout = QVBoxLayout(wrapper)
        self.layout.addWidget(self.manga_view)

        self.setCentralWidget(wrapper)

    def confirmQuit(self):
        reply = QMessageBox.question(
            self,
            "Quit?",
            "Are you sure you want to exit?",
        )
        return reply == QMessageBox.Yes

    def closeEvent(self, event):
        if self.confirmQuit():
            self.cache.close()
            event.accept()
        else:
            event.ignore()

    def selectedManga(self, manga_item):
        prev_widget = self.manga_view.widget(self.manga_view.count() - 1)
        prev_widget.hide()
        prev_widget.deleteLater()

        desc = QLabel(manga_item.meta.desc)
        desc.setWordWrap(True)

        self.manga_view.addWidget(desc)


class LoadingSplash(QSplashScreen):
    def showMessage(self, message):
        super().showMessage(
            f"\ntankobon v{__version__}\nCopyright (c) 2020-2021 Ong Yong Xin\n{message}",
            Qt.AlignBottom,
            Qt.white,
        )


if __name__ == "__main__":

    # splash = LoadingSplash(LOGO)
    # splash.show()

    # splash.showMessage("Loading manga metadata...")

    window = Root()

    # splash.showMessage("This splash screen is nice, right?")

    # time.sleep(2.5)

    window.show()
    # splash.finish(window)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(_app.exec_())
