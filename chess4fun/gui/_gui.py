# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import sys

import PySide2
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout

class web_engine_page(QWebEnginePage):
    def __init__(self, profile, parent):
        super().__init__(profile, parent) # parent=None
    def javaScriptConsoleMessage(self, *args, **kwargs):
        pass

class web_view(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.web_engine_profile = QWebEngineProfile()
        self.web_engine_page = web_engine_page(profile=self.web_engine_profile, parent=self)
        self.setPage(self.web_engine_page)
        if not self.page().profile().isOffTheRecord():
            raise RuntimeError("the profile should be off-the-record.")


class app_window(QMainWindow):
    def __init__(self, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        # screen
        screen = self.app.primaryScreen()
        self.dpi = 72/screen.devicePixelRatio()
        self.width = screen.availableGeometry().width() * 1.00
        self.height = screen.availableGeometry().height() * 0.80
        # central widget
        self.UI = UI(app_window=self, dpi=self.dpi)
        self.setCentralWidget(self.UI)
        self.setWindowTitle("Chess for fun!")
        self.resize(self.width, self.height)

class UI(QWidget):
    def __init__(self, app_window=None, dpi=None, *args, **kwargs):
        super().__init__(parent=app_window, *args, **kwargs)
        self.app_window = app_window
        self.webview = web_view(parent=self)
        import chess
        import chess.svg
        board = chess.Board("8/8/8/8/4N3/8/8/8 w - - 0 1")
        squares = board.attacks(chess.E4)
        self.webview.setHtml(chess.svg.board(board, squares=squares, size=350))
        self.layout = QGridLayout()
        self.layout.addWidget(self.webview, 0, 0, 1, 1)
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)
    window = app_window(app=app)
    window.show()
    app.exec_()

