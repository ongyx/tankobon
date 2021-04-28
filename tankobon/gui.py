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
    QSplashScreen,
    QWidget,
)

from . import core, parsers  # noqa: F401
from .__version__ import __version__

_app = QApplication([])

MAX_COL = 5
LOGO = QPixmap("logo.jpg")


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

        # actual tankobon api
        self.cache = core.Cache()

        # we show manga in a grid layout
        grid_widget = QWidget(self)
        self.grid = QGridLayout(grid_widget)

        self.row = 0
        self.col = 0

        # cache metadata of all manga in cache
        self.metacache = {}
        for url in self.cache.index:
            manga = self.cache.load(url)
            self.metacache[manga.url] = manga.meta

            self.addPreview(manga)

        self.setCentralWidget(grid_widget)

    def addPreview(self, manga: core.Manga):
        manga_path = (self.cache.path / self.cache._hashpath(manga)).with_suffix("")
        manga_path.mkdir(exist_ok=True)

        label = QLabel(manga.title, self)

        try:
            # the cover may not be a jpg or a png, so just ignore extension
            cover_path = manga_path / next(manga_path.glob("cover.*"))

        except StopIteration:
            # cover does not exist, don't show
            pass

        else:
            cover = QPixmap(str(cover_path))
            # cover = cover.scaled(label.size(), Qt.KeepAspectRatio)

            label.setPixmap(cover)

        if self.col >= 5:
            self.col = 0

        self.grid.addWidget(label, self.row, self.col)

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
