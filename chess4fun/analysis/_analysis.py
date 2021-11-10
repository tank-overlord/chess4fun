# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import asyncio
import chess
import chess.engine

async def evaluate_position(board: chess.Board = None) -> None:
    from ..gui import preferences
    if preferences['chess_engine_exe_path'] is None:
        return None
    transport, engine = await chess.engine.popen_uci(command=preferences['chess_engine_exe_path'])
    await engine.configure({"Hash": preferences['chess_engine_hash_size']})
    info = await engine.analyse(board, chess.engine.Limit(time=preferences['chess_engine_search_time']))
    await engine.quit()
    return info

async def advise_move(board: chess.Board = None) -> None:
    from ..gui import preferences
    if preferences['chess_engine_exe_path'] is None:
        return None
    transport, engine = await chess.engine.popen_uci(command=preferences['chess_engine_exe_path'])
    await engine.configure({"Hash": preferences['chess_engine_hash_size']})
    if not board.is_game_over():
        result = await engine.play(board, chess.engine.Limit(time=preferences['chess_engine_search_time']))
    await engine.quit()
    return result
