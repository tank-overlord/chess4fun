# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import chess, chess.pgn, pathlib, os, pickle

opening_book_filename = 'scideco_opening.pkl'

def preprocess_ECO_book():
    """
    This only be run once.
    "scideco.pgn" can be obtained by running "eco2pgn.py scid.eco > scideco.pgn",
    while "eco2pgn.py" and "scid.eco" can be downloaded from: https://sourceforge.net/projects/scidvspc/
    https://sourceforge.net/projects/scidvspc/files/source/scid_vs_pc-4.21.tgz/download (GPL licensed)
    """
    #curr_dir = pathlib.Path(__file__).parent.absolute()
    #os.chdir(curr_dir)
    opening_book_dict = {}
    pgn = open("scideco.pgn") 
    while True:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break
        Mainline_moves_str = game.accept(chess.pgn.StringExporter(headers=False,variations=False,comments=False)).replace('\n', ' ')
        opening_book_dict[Mainline_moves_str] = {'ECO': game.headers.get('ECO', '?'),'Variation': game.headers.get('Variation', '?')}
    with open(opening_book_filename, 'wb') as opening_book_file:
        pickle.dump(opening_book_dict, opening_book_file)

curr_dir = pathlib.Path(__file__).parent.absolute()
os.chdir(curr_dir)
with open(opening_book_filename, 'rb') as opening_book_file:
    opening_book_dict = pickle.load(opening_book_file)

def find_opening(move_stack: list = None):
    n_plys = len(move_stack)
    for n_ply_back in range(n_plys):
        san = chess.Board().variation_san(move_stack[:(n_plys-n_ply_back)]) + " *"
        if san in opening_book_dict.keys():
            return opening_book_dict[san]