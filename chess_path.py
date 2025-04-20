# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np

from power import Power
from square import Square
from piece import *

class ChessPath:
    def __init__(self, piece, landing_square):
        self.piece = piece
        self.start = self.piece.square
        self.land = landing_square
        
        self.valid, self.intermediate_squares = ChessPath.validate_path(self.piece, self.start, self.land)
    
    def validate_path(piece, start, land):
        valid = False
        intermediate_squares = []
        dfile = land.file - start.file
        drank = land.rank - start.rank
        dfile_sign = 1 if dfile >= 0 else -1
        drank_sign = 1 if drank >= 0 else -1
        file_range = range(start.file, land.file, dfile_sign)[1:]
        rank_range = range(start.rank, land.rank, drank_sign)[1:]
        match piece.code:
            case Piece.KING:
                if abs(dfile) <= 1 and abs(drank) <= 1:
                    valid = True
            case Piece.ROOK:
                if dfile == 0:
                    intermediate_squares = [Square(rank=y, file=start.file) for y in rank_range]
                    valid = True
                elif drank == 0:
                    intermediate_squares = [Square(rank=start.rank, file=x) for x in file_range]
                    valid = True
            case Piece.BISHOP:
                if abs(dfile) == abs(drank):
                    intermediate_squares = [Square(file=x, rank=y) for x, y in zip(file_range, rank_range)]
                    valid = True
            case Piece.KNIGHT:
                if (abs(drank) == 2 and abs(dfile) == 1) or (abs(dfile) == 2 and abs(drank) == 1):
                    valid = True
            case Piece.PAWN:
                
                
                home_rank_pawn = True
                if piece.power.side == Power.WHITE:
                    if drank == 1 and abs(dfile) <= 1:
                        valid = True
                    elif start.rank < 2 and drank == 2 and dfile == 0:
                        intermediate_squares.append(Square(rank=start.rank + 1, file=start.file))
                        valid = True
                elif piece.power.side == Power.BLACK:
                    print(drank, dfile, start.rank)
                    if drank == -1 and abs(dfile) <= 1:
                        valid = True
                    elif start.rank >= 6 and drank == -2 and dfile == 0:
                        intermediate_squares.append(Square(rank=start.rank - 1, file=start.file))
                        valid = True
            case _:
                pass
        return valid, intermediate_squares