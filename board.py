# -*-coding:utf8-*-

from collections import namedtuple
from enum import Enum
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np

from square import Square
from piece import Piece
from power import Side

class Board:
    default_sc_mask = np.array([
        [1, 1, 0, 1, 1, 1, 0, 1],
        [0, 0, 1, 0, 1, 0, 0, 1],
        [0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 1, 0, 1, 0, 0, 0],
        [1, 1, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1, 1, 0, 0, 0],
        [1, 0, 1, 1, 1, 0, 1, 1]
    ], dtype=bool)
    
    def __init__(self, powers, sc_mask=None):
        if sc_mask is None:
            self.sc_mask = Board.default_sc_mask
        else:
            self.sc_mask = sc_mask
        
        self.powers = powers
        self.pieces = []
        self.ownership = np.zeros((8, 8), dtype=int)
        self.sc_ownership = np.zeros((8, 8), dtype=int)# -1 for white, -2 for black
        self.sc_ownership[:2][self.sc_mask[:2]] = Side.WHITE
        self.sc_ownership[-2:][self.sc_mask[-2:]] = Side.BLACK
        
    def set_ownership(self, square, power):
        old_code = self.ownership[square.rank, square.file]
        new_code = power.get_code()
        if old_code != new_code:
            self.ownership[square.rank, square.file] = new_code
            return True
        return False
    
    def set_sc_ownership(self, square, power):
        old_code = self.sc_ownership[square.rank, square.file]
        new_code = power.get_code()
        if old_code != new_code:
            self.sc_ownership[square.rank, square.file] = power.get_code()
            return True
        return False
    
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
        

class BoardArtist:
    """
    Squares and supply centers
    """
    def __init__(self, board):
        self.board = board
        self.ax = None
        
        self.light_mask = np.ones((8, 8), dtype=bool)
        self.light_mask[::2, ::2] = False
        self.light_mask[1::2, 1::2] = False
        
        self.sc_xshift, self.sc_yshift = -.35, -.35
        self.sc_radius = .08
        
        self.square_artists = np.full((8, 8), None, dtype=object)
        self.sc_artists = np.full((8, 8), None, dtype=object)
    
    def add_to_ax(self, ax):
        self.ax = ax
        self.ax.tick_params(bottom=False, top=False, left=False, right=False)
        self.ax.set_xticks([0, 1, 2, 3, 4, 5, 6, 7], ["a", "b", "c", "d", "e", "f", "g", "h"])
        self.ax.set_yticks([0, 1, 2, 3, 4, 5, 6, 7], ["1", "2", "3", "4", "5", "6", "7", "8"])
        self.ax.set_aspect("equal")
        self.ax.set_xlim(-.5, 7.5)
        self.ax.set_ylim(-.5, 7.5)
        
        self.populate_square_artists(self.square_artists)
        self.populate_sc_artists(self.sc_artists)
        for square_artist in self.square_artists.flat:
            if square_artist is not None:
                self.ax.add_patch(square_artist)
        for sc_artist in self.sc_artists.flat:
            if sc_artist is not None:
                self.ax.add_patch(sc_artist)
    
    def populate_square_artists(self, square_artists):
        for rank in range(8):
            for file in range(8):
                patch = self.make_square_patch(Square(rank=rank, file=file))
                square_artists[rank, file] = patch
    
    def populate_sc_artists(self, sc_artists):
        for rank, file in zip(*self.board.sc_mask.nonzero()):
            power = self.board.powers[self.board.sc_ownership[rank, file]]
            patch = self.make_sc_patch(Square(rank=rank, file=file), power)
            sc_artists[rank, file] = patch
    
    def make_square_patch(self, square):
        rank, file = square.rank, square.file
        fc = self.get_square_fc(square, self.board.powers[0])
        patch = mpl.patches.Rectangle((file - .5, rank - .5), 1, 1, fc=fc, ec="none")
        return patch
    
    def make_sc_patch(self, square, power):
        rank, file = square.rank, square.file
        fc = self.get_square_fc(square, power)
        patch = mpl.patches.Circle((file + self.sc_xshift, rank + self.sc_yshift), radius=self.sc_radius, fc=fc, ec="k", lw=1.5)
        return patch
    
    def get_square_fc(self, square, power):
        rank, file = square.rank, square.file
        fc = power.square_color[int(self.light_mask[rank, file])]
        return fc
    
    def set_owner(self, square, power):
        fc = self.get_square_fc(square, power)
        self.square_artists[square.rank, square.file].set_fc(fc)
    
    def set_sc_owner(self, square, power):
        fc = self.get_square_fc(square, power)
        self.sc_artists[square.rank, square.file].set_fc(fc)