# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from piece import Piece, PieceArtist
from board import BoardArtist
from order import *

class Visualizer:
    def __init__(self):
        mpl.rcParams['toolbar'] = 'None'
        self.fig, self.ax = plt.subplots(1, 1, layout="tight")
        self.board_artist = None
        
        self.piece_kwargs = {"lw": 2, "capstyle": "butt", "joinstyle": "round"}
        r = .3
        self.piece_radius = {
            Piece.PAWN: .2,
            Piece.KNIGHT: r,
            Piece.BISHOP: r,
            Piece.ROOK: r,
            Piece.KING: r
        }
        
        self.square_artists = np.full((8, 8), None, dtype=object)
        self.sc_artists = np.full((8, 8), None, dtype=object)
    
    def ion(self):
        plt.ion()
    
    def ioff(self):
        plt.ioff()
    
    def show(self):
        plt.show()
    
    def render(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def make_piece_artist(self, piece):
        return PieceArtist(self, piece)
    
    def add_piece(self, piece):
        piece.artist.add_to_ax(self.ax)
    
    def erase_piece(self, piece):
        piece.artist.remove()
    
    def move_piece(self, piece, square):
        piece.artist.move_to(square)
    
    def set_piece_status(self, piece, status):
        pass
    
    def draw_board(self, board):
        self.board_artist = BoardArtist(self, board)
        self.board_artist.populate_square_artists(self.square_artists)
        self.board_artist.populate_sc_artists(self.sc_artists)
        for square_artist in self.square_artists.flat:
            if square_artist is not None:
                self.ax.add_patch(square_artist)
        for sc_artist in self.sc_artists.flat:
            if sc_artist is not None:
                self.ax.add_patch(sc_artist)
    
    def set_square_owner(self, square, power):
        fc = self.board_artist.get_square_fc(square, power)
        self.square_artists[square.rank, square.file].set_fc(fc)
    
    def set_sc_owner(self, square, power):
        fc = self.board_artist.get_square_fc(square, power)
        self.sc_artists[square.rank, square.file].set_fc(fc)
    
    def make_order_artist(self, order):
        if isinstance(order, HoldOrder):
            return HoldOrderArtist(order)
        elif isinstance(order, MoveOrder):
            return MoveOrderArtist(order)
        elif isinstance(order, BuildOrder):
            return BuildOrderArtist(order)
        elif isinstance(order, DisbandOrder):
            return DisbandOrderArtist(order)
        elif isinstance(order, SupportHoldOrder):
            return SupportHoldOrderArtist(order)
        else:
            raise ValueError(f"No artist for {order}!")
    
    def add_order(self, order):
        order.artist.add_to_ax(self.ax)
    
    def erase_order(self, order):
        order.artist.remove()