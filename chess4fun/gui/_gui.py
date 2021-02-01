# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import sys

import PySide6

from PySide6.QtWidgets import QApplication, QMainWindow

class app_window(QMainWindow):
    def __init__(self, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app

def main():
    app = QApplication(sys.argv)
    window = app_window(app=app)
    window.show()
    app.exec_()

