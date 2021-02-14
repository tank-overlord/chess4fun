# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import sys

import PySide2
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QDialog, QPushButton, QTextBrowser, QAction, QLabel, QFileDialog, QLineEdit, QCheckBox
from PySide2.QtSvg import QSvgWidget
from PySide2.QtCore import QThread, Signal

import asyncio
import chess
import chess.svg
import chess.engine

asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy()) # https://python-chess.readthedocs.io/en/latest/engine.html

from ..opening import find_opening
from ..analysis import advise_move

import pathlib
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
pygame.mixer.init()

# sound
sound_dir = pathlib.Path(__file__).parent.absolute() / 'sound'

# https://freesound.org/people/Splashdust/sounds/67454/
# https://creativecommons.org/publicdomain/zero/1.0/
illegal_move_sound = pygame.mixer.Sound(sound_dir / "illegal_move.wav")

# https://freesound.org/people/mh2o/sounds/351518/
# https://creativecommons.org/publicdomain/zero/1.0/
piece_move_sound = pygame.mixer.Sound(sound_dir / "piece_move.wav")

check_sound = pygame.mixer.Sound(sound_dir / "check.wav")
check_mate_sound = pygame.mixer.Sound(sound_dir / "check_mate.wav")
stalemate_sound = pygame.mixer.Sound(sound_dir / "stalemate.wav")
insufficient_material_sound = pygame.mixer.Sound(sound_dir / "insufficient_material.wav")
gameover_sound = pygame.mixer.Sound(sound_dir / "gameover.wav")

illegal_move_sound.set_volume(1.0)
piece_move_sound.set_volume(1.0)
check_sound.set_volume(1.0)
check_mate_sound.set_volume(1.0)
stalemate_sound.set_volume(1.0)
insufficient_material_sound.set_volume(1.0)
gameover_sound.set_volume(1.0)

# preference settings (default)
preferences = {'chess_engine_exe_path': '/usr/local/bin/stockfish', 
               'chess_engine_search_time': 5.0,
               'play_sound': True}


class preferences_dialog(QDialog):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle("Preference Settings")
        self.app_window = parent
        #
        if not pathlib.Path(preferences['chess_engine_exe_path']).is_file():
            preferences['chess_engine_exe_path'] = None
            self.app_window.UI.advise_next_pushbutton.setEnabled(False)
            self.app_window.UI.self_play_pushbutton.setEnabled(False)
        self.chess_engine_exe_path_label = QLabel('- Chess engine (stockfish) executable path:', parent=self)
        self.chess_engine_exe_path_pushbutton = QPushButton(f"{preferences['chess_engine_exe_path']}", parent=self)
        self.chess_engine_exe_path_pushbutton.clicked.connect(self._change_chess_engine_path)
        #
        self.chess_engine_search_time_label = QLabel('- Chess engine search time (sec):', parent=self)
        self.chess_engine_search_time_lineedit = QLineEdit(parent=self)
        self.chess_engine_search_time_lineedit.setText(f"{preferences['chess_engine_search_time']}")
        self.chess_engine_search_time_lineedit.textChanged.connect(self._change_chess_engine_search_time)
        #
        self.play_sound_label = QLabel('- Play sound effect?', parent = self)
        self.play_sound_checkbox = QCheckBox('Yes', parent=self)
        self.play_sound_checkbox.setChecked(preferences['play_sound'])
        self.play_sound_checkbox.stateChanged.connect(self._play_sound_state_changed)
        #
        self.layout = QGridLayout()
        self.layout.addWidget(self.chess_engine_exe_path_label, 0, 0)
        self.layout.addWidget(self.chess_engine_exe_path_pushbutton, 0, 1)
        self.layout.addWidget(self.chess_engine_search_time_label, 1, 0)
        self.layout.addWidget(self.chess_engine_search_time_lineedit, 1, 1)
        self.layout.addWidget(self.play_sound_label, 2, 0)
        self.layout.addWidget(self.play_sound_checkbox, 2, 1)
        self.setLayout(self.layout)
        #
        self.chess_engine_exe_path_filedialog = QFileDialog(parent=self)
        self.chess_engine_exe_path_filedialog.setNameFilters(["All files (*.*)",])
        self.chess_engine_exe_path_filedialog.selectNameFilter("All files (*.*)")

    def _change_chess_engine_path(self):
        self.chess_engine_exe_path_filedialog.exec_()
        selectedFiles = self.chess_engine_exe_path_filedialog.selectedFiles()
        if len(selectedFiles) > 0:
            preferences['chess_engine_exe_path'] = self.chess_engine_exe_path_filedialog.selectedFiles()[0]
            self.chess_engine_exe_path_pushbutton.setText(f"{preferences['chess_engine_exe_path']}")
            self.app_window.UI.advise_next_pushbutton.setEnabled(True)
            self.app_window.UI.self_play_pushbutton.setEnabled(True)

    def _change_chess_engine_search_time(self, new_text):
        try:
            preferences['chess_engine_search_time'] = float(new_text)
        except:
            pass

    def _play_sound_state_changed(self, state: int):
        preferences['play_sound'] = self.play_sound_checkbox.isChecked()


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
        self.setGeometry(0, 0, 600, 850)
        #print(self.geometry())
        #self.resize(self.width, self.height)
        self.preferences_dialog = preferences_dialog(parent=self)
        # preferences
        prefAct = QAction('&Preferences...', parent=self)
        prefAct.setShortcut('Ctrl+,')
        prefAct.setStatusTip('Preference settings')
        prefAct.triggered.connect(self.preferences_dialog.exec_)
        # exit
        exitAct = QAction('&Exit', parent=self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit app')
        exitAct.triggered.connect(self.app.quit)
        # menubar
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        self.AppMenu = self.menubar.addMenu('&App')
        self.AppMenu.addAction(prefAct)
        self.AppMenu.addAction(exitAct)


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
        self.promotion = None # default
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
    

class self_play_thread(QThread):
    _signal = Signal(chess.Move)
    def __init__(self, board: chess.Board = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = board.copy()
    def run(self):
        while not self.board.is_game_over():
            result = asyncio.run(advise_move(self.board))
            self._signal.emit(result.move)
            self.board.push(result.move)


class chess_board_widget(QSvgWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.UI = parent
        self.board_size = 600
        self.setGeometry(0, 0, self.board_size, self.board_size)
        self.promotion_dialog = PromotionDialog(parent=self)
        self.new_game()
        self.move_stack = []
        self.turn_dict = {chess.WHITE: 'White', chess.BLACK: 'Black'}

    def update_text_browser(self):
        opening = find_opening(self.move_stack[:self.last_legal_move_ply_index])
        san = chess.Board().variation_san(self.move_stack[:self.last_legal_move_ply_index])
        if opening is None:
            self.UI.text_browser.setHtml(f"{san}")
        else:
            self.UI.text_browser.setHtml(f"[ECO \"{opening['ECO']}\"]<br/>[Variation \"{opening['Variation']}\"]<br/><br/>{san}")

    def new_game(self):
        self.board = chess.Board()
        self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size).encode("UTF-8"))
        self._square_selected = False
        #self.move_stack = []
        self.last_legal_move_ply_index = 0
        self.promotion_dialog.promotion = chess.QUEEN
        self.UI.text_browser.setHtml("")
        self.repaint()

    def move_back(self):
        if self.last_legal_move_ply_index > 0:
            self.last_legal_move_ply_index -= 1
            self.board.pop()
            self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size).encode("UTF-8"))
            self.update_text_browser()
            self.repaint()

    def move_forward(self):
        if self.last_legal_move_ply_index < len(self.move_stack):
            next_move = self.move_stack[self.last_legal_move_ply_index]
            if next_move in self.board.legal_moves:
                self.board.push(next_move)
                self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size).encode("UTF-8"))
                self.last_legal_move_ply_index += 1
                self.update_text_browser()
                self.repaint()

    def analyze_prev(self):
        self.UI.text_browser.setHtml(f"Coming Soon!")
        self.repaint()

    def self_play(self):
        self.selfplay_thread = self_play_thread(board = self.board)
        self.selfplay_thread._signal.connect(self.make_this_move)
        self.selfplay_thread.start()

    def make_this_move(self, this_move: chess.Move = None):
        if this_move not in self.board.legal_moves:
            raise RuntimeError(f"this_move {this_move} is illegal in the current position FEN: [{self.board.fen()}]")
        if self.last_legal_move_ply_index < len(self.move_stack):
            self.move_stack[self.last_legal_move_ply_index] = this_move
        else:
            self.move_stack.append(this_move)
        self.last_legal_move_ply_index += 1
        self.update_text_browser()
        self.board.push(this_move)
        self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size, lastmove=this_move).encode("UTF-8"))
        if preferences['play_sound']:
            piece_move_sound.play()
        if self.board.is_game_over():
            if self.board.is_insufficient_material():
                if preferences['play_sound']:
                    insufficient_material_sound.play()
            elif self.board.is_checkmate():
                self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size, check=self.board.king(self.board.turn), lastmove=this_move).encode("UTF-8"))
                if preferences['play_sound']:
                    check_mate_sound.play()
            elif self.board.is_stalemate():
                if preferences['play_sound']:
                    stalemate_sound.play()
            else:
                if preferences['play_sound']:
                    gameover_sound.play()
        elif self.board.is_check():
            self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size, check=self.board.king(self.board.turn), lastmove=this_move).encode("UTF-8"))
            if preferences['play_sound']:
                check_sound.play()

    def advise_next(self):
        if self.board.is_game_over():
            html_str = "game over"
        else:
            result = asyncio.run(advise_move(self.board))
            if result is not None:
                if result.draw_offered:
                    html_str = f"{self.turn_dict[self.board.turn]} to offer draw"
                elif result.resigned:
                    html_str = f"{self.turn_dict[self.board.turn]} to resign"
                else:
                    self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size, arrows=[(result.move.from_square, result.move.to_square)]).encode("UTF-8"))
                    html_str = f"{self.turn_dict[self.board.turn]} to move {chess.piece_name(self.board.piece_type_at(result.move.from_square))} from {chess.square_name(result.move.from_square)} to {chess.square_name(result.move.to_square)}"
                    if result.move.promotion is not None:
                        html_str += f" and promote it to {chess.piece_name(result.move.promotion)}"
                    if result.ponder is not None:
                        html_str += f"<br/>Ponder: {self.turn_dict[not self.board.turn]} to move {chess.piece_name(self.board.piece_type_at(result.ponder.from_square))} from {chess.square_name(result.ponder.from_square)} to {chess.square_name(result.ponder.to_square)}"
                        if result.ponder.promotion is not None:
                            html_str += f" and promote it to {chess.piece_name(result.ponder.promotion)}"
            else:
                html_str = ""
        self.UI.text_browser.setHtml(html_str)
        self.repaint()

    def mouseMoveEvent(self, event):
        #print(f"move: {event.pos()}")
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        _file_idx =     (event.pos().x() // int(self.geometry().width()/8))    # 'A' - 'H', col
        _rank_idx = 7 - (event.pos().y() // int(self.geometry().height()/8))   # 1 - 8, row
        _square = chess.square(_file_idx, _rank_idx)
        #print(f"press: {event.pos()}")
        #print(f"{chess.square_name(_square)}")
        self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size, arrows=[(_square, _square)]).encode("UTF-8"))
        self._square_selected = True
        self._from_square = _square
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        _file_idx =     (event.pos().x() // int(self.geometry().width()/8))    # 'A' - 'H', col
        _rank_idx = 7 - (event.pos().y() // int(self.geometry().height()/8))   # 1 - 8, row
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
                    self.make_this_move(this_move)
                else:
                    self.load(chess.svg.board(self.board, coordinates=False, size=self.board_size, ).encode("UTF-8"))
                    if preferences['play_sound']:
                        illegal_move_sound.play()
                self._square_selected = False
        #print(f"released: {event.pos()}")
        super().mouseReleaseEvent(event)


class UI(QWidget):
    def __init__(self, app_window=None, dpi=None, *args, **kwargs):
        super().__init__(parent=app_window, *args, **kwargs)
        self.app_window = app_window
        self.text_browser = QTextBrowser(parent=self)
        self.chessboard_widget  = chess_board_widget(parent=self)
        self.new_pushbutton     = QPushButton('New',parent=self)
        self.back_pushbutton    = QPushButton('Back',parent=self)
        self.forward_pushbutton = QPushButton('Forward',parent=self)
        self.analyze_prev_pushbutton = QPushButton('Analyze Prev', parent=self)
        self.advise_next_pushbutton  = QPushButton('Advise Next',parent=self)
        self.self_play_pushbutton = QPushButton('Self Play', parent=self)
        self.layout = QGridLayout()
        self.layout.addWidget(self.chessboard_widget,  0, 0, 1, 5)
        self.layout.addWidget(self.new_pushbutton,     1, 0, 1, 1)
        self.layout.addWidget(self.back_pushbutton,    1, 1, 1, 1)
        self.layout.addWidget(self.forward_pushbutton, 1, 2, 1, 1)
        self.layout.addWidget(self.analyze_prev_pushbutton, 1, 3, 1, 1)
        self.layout.addWidget(self.advise_next_pushbutton,  1, 4, 1, 1)
        self.layout.addWidget(self.self_play_pushbutton, 2, 0, 1, 1 )
        self.layout.addWidget(self.text_browser,       3, 0, 1, 5)
        self.setLayout(self.layout)
        self.new_pushbutton.clicked.connect(self.chessboard_widget.new_game)
        self.back_pushbutton.clicked.connect(self.chessboard_widget.move_back)
        self.forward_pushbutton.clicked.connect(self.chessboard_widget.move_forward)
        self.analyze_prev_pushbutton.clicked.connect(self.chessboard_widget.analyze_prev)
        self.advise_next_pushbutton.clicked.connect(self.chessboard_widget.advise_next)
        self.self_play_pushbutton.clicked.connect(self.chessboard_widget.self_play)
        #
        self.analyze_prev_pushbutton.setEnabled(False)

    
def main():
    app = QApplication(sys.argv)
    window = app_window(app=app)
    window.show()
    app.exec_()

