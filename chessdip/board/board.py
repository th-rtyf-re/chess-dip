# -*-coding:utf8-*-

import numpy as np

from chessdip.board.piece import Piece
from chessdip.board.power import Side

class Board:
    def __init__(self, setup):
        self.sc_mask = setup.sc_mask
        self.powers = setup.powers
        self.pieces = []
        self.ownership = np.zeros((8, 8), dtype=int)
        self.sc_ownership = np.zeros((8, 8), dtype=int)
        self.sc_ownership[:2][self.sc_mask[:2]] = Side.WHITE
        self.sc_ownership[-2:][self.sc_mask[-2:]] = Side.BLACK
    
    def set_ownership(self, square, power):
        old_code = self.ownership[square.rank, square.file]
        new_code = self.powers.index(power)
        if old_code != new_code:
            self.ownership[square.rank, square.file] = new_code
            return True
        return False
    
    def set_sc_ownership(self, square, power):
        if not self.sc_mask[square.rank, square.file]:
            return False
        old_code = self.sc_ownership[square.rank, square.file]
        new_code = self.powers.index(power)
        if old_code != new_code:
            self.sc_ownership[square.rank, square.file] = self.powers.index(power)
            return True
        return False
    
    def get_default_owner(self, square):
        return self.powers[Side.NEUTRAL]
    
    def get_default_sc_owner(self, square):
        if square.rank < 2:
            return self.powers[Side.WHITE]
        elif square.rank >= 6:
            return self.powers[Side.BLACK]
        else:
            return self.powers[Side.NEUTRAL]
    
    def add_piece(self, code, power, square):
        piece = Piece(code, power, square, self.visualizer)
        self.pieces.append(piece)
        self.set_ownership(square, power)
        return piece
    
    def remove_piece(self, piece):
        piece.remove()
        self.pieces.remove(piece)
    
    def get_piece(self, square):
        for piece in self.pieces:
            if piece.square == square:
                return piece
        return None
    
    def vacate_square(self, square):
        for piece in self.pieces:
            if piece.square == square:
                self.remove_piece(piece)
    
    def move_piece_to(self, piece, square):
        piece.move_to(square)
        self.set_ownership(square, piece.power)