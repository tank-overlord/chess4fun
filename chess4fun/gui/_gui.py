# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import sys

import PySide2
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QDialog, QPushButton
from PySide2.QtSvg import QSvgWidget

import chess
import chess.svg

import pathlib
import os

import pygame

pygame.mixer.init()

curr_dir = pathlib.Path(__file__).parent.absolute()
os.chdir(curr_dir)

# https://freesound.org/people/Splashdust/sounds/67454/
# https://creativecommons.org/publicdomain/zero/1.0/
illegal_move_sound = pygame.mixer.Sound("illegal_move.wav")

# https://freesound.org/people/mh2o/sounds/351518/
# https://creativecommons.org/publicdomain/zero/1.0/
piece_move_sound = pygame.mixer.Sound("piece_move.wav")

check_sound = pygame.mixer.Sound("check.wav")
check_mate_sound = pygame.mixer.Sound("check_mate.wav")
stalemate_sound = pygame.mixer.Sound("stalemate.wav")
insufficient_material_sound = pygame.mixer.Sound("insufficient_material.wav")
gameover_sound = pygame.mixer.Sound("gameover.wav")

illegal_move_sound.set_volume(1.0)
piece_move_sound.set_volume(1.0)
check_sound.set_volume(1.0)
check_mate_sound.set_volume(1.0)
stalemate_sound.set_volume(1.0)
insufficient_material_sound.set_volume(1.0)
gameover_sound.set_volume(1.0)

class app_window(QMainWindow):
    def __init__(self, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        # screen
        screen = self.app.primaryScreen()
        self.dpi = 72/screen.devicePixelRatio()
        #self.width = screen.availableGeometry().width() * 0.60
        #self.height = screen.availableGeometry().height() * 0.60
        # central widget
        self.UI = UI(app_window=self, dpi=self.dpi)
        self.setCentralWidget(self.UI)
        self.setWindowTitle("Chess for fun!")
        #self.resize(self.width, self.height)


class PromotionDialog(QDialog):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.resize(200,100)
        self.setWindowTitle("Promotion")
        self.queen_promotion_pushbutton = QPushButton('Queen', parent=self)
        self.rook_promotion_pushbutton = QPushButton('Rook', parent=self)
        self.bishop_promotion_pushbutton = QPushButton('Bishop', parent=self)
        self.knight_promotion_pushbutton = QPushButton('Knight', parent=self)
        self.layout = QGridLayout()
        self.layout.addWidget(self.queen_promotion_pushbutton,  0, 0)
        self.layout.addWidget(self.rook_promotion_pushbutton ,  1, 0)
        self.layout.addWidget(self.bishop_promotion_pushbutton, 2, 0)
        self.layout.addWidget(self.knight_promotion_pushbutton, 3, 0)
        self.setLayout(self.layout)
        self.promotion = chess.QUEEN # default
        self.queen_promotion_pushbutton.clicked.connect(self._queen_promotion)
        self.rook_promotion_pushbutton.clicked.connect(self._rook_promotion)
        self.bishop_promotion_pushbutton.clicked.connect(self._bishop_promotion)
        self.knight_promotion_pushbutton.clicked.connect(self._knight_promotion)

    def _queen_promotion(self):
        self.promotion = chess.QUEEN
        self.hide()

    def _rook_promotion(self):
        self.promotion = chess.ROOK
        self.hide()

    def _bishop_promotion(self):
        self.promotion = chess.BISHOP
        self.hide()

    def _knight_promotion(self):
        self.promotion = chess.KNIGHT
        self.hide()
    

class chess_board_widget(QSvgWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = chess.Board()
        self.load(chess.svg.board(self.board, coordinates=False, size=600).encode("UTF-8"))
        self._square_selected = False
        self.promotion_dialog = PromotionDialog(parent=self)
        self.variation = []

    def mouseMoveEvent(self, event):
        #print(f"move: {event.pos()}")
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        _file_idx =     (event.pos().x() // 75)   # 'A' - 'H', col
        _rank_idx = 7 - (event.pos().y() // 75)   # 1 - 8, row
        _square = chess.square(_file_idx, _rank_idx)
        #print(f"press: {event.pos()}")
        #print(f"{chess.square_name(_square)}")
        self.load(chess.svg.board(self.board, coordinates=False, size=600, arrows=[(_square, _square)]).encode("UTF-8"))
        self._square_selected = True
        self._from_square = _square
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        global illegal_move_sound
        _file_idx =     (event.pos().x() // 75)   # 'A' - 'H', col
        _rank_idx = 7 - (event.pos().y() // 75)   # 1 - 8, row
        _square = chess.square(_file_idx, _rank_idx)
        if self._square_selected:
            self._to_square = _square
            if self._from_square != self._to_square:
                this_potential_promotion_move = chess.Move(from_square = self._from_square, to_square = self._to_square, promotion = chess.QUEEN)
                if this_potential_promotion_move in self.board.legal_moves:
                    self.promotion_dialog.exec_()
                    this_move = chess.Move(from_square = self._from_square, to_square = self._to_square, promotion = self.promotion_dialog.promotion)
                else:
                    this_move = chess.Move(from_square = self._from_square, to_square = self._to_square, promotion = None)
                if this_move in self.board.legal_moves:
                    self.variation.append(this_move)
                    print(f"\nthis move (UCI): {this_move.uci()}\nSAN: {chess.Board().variation_san(self.variation)}")
                    self.board.push(this_move)
                    if self.board.is_game_over():
                        if self.board.is_insufficient_material():
                            self.load(chess.svg.board(self.board, coordinates=False, size=600, lastmove=this_move).encode("UTF-8"))
                            insufficient_material_sound.play()
                        elif self.board.is_checkmate():
                            self.load(chess.svg.board(self.board, coordinates=False, size=600, check=self.board.king(self.board.turn), lastmove=this_move).encode("UTF-8"))
                            check_mate_sound.play()
                        elif self.board.is_stalemate():
                            self.load(chess.svg.board(self.board, coordinates=False, size=600, lastmove=this_move).encode("UTF-8"))
                            stalemate_sound.play()
                        else:
                            self.load(chess.svg.board(self.board, coordinates=False, size=600, lastmove=this_move).encode("UTF-8"))
                            gameover_sound.play()
                    elif self.board.is_check():
                        self.load(chess.svg.board(self.board, coordinates=False, size=600, check=self.board.king(self.board.turn), lastmove=this_move).encode("UTF-8"))
                        check_sound.play()
                    else:
                        self.load(chess.svg.board(self.board, coordinates=False, size=600, lastmove=this_move).encode("UTF-8"))
                        piece_move_sound.play()
                else:
                    self.load(chess.svg.board(self.board, coordinates=False, size=600, ).encode("UTF-8"))
                    illegal_move_sound.play()
                self._square_selected = False
        #print(f"released: {event.pos()}")
        super().mouseReleaseEvent(event)


class UI(QWidget):
    def __init__(self, app_window=None, dpi=None, *args, **kwargs):
        super().__init__(parent=app_window, *args, **kwargs)
        self.app_window = app_window
        self.chessboard_widget = chess_board_widget(parent=self)
        self.layout = QGridLayout()
        self.layout.addWidget(self.chessboard_widget, 0, 0, 1, 1)
        self.setLayout(self.layout)


def main():
    app = QApplication(sys.argv)
    window = app_window(app=app)
    window.show()
    app.exec_()

