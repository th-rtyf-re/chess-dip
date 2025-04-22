# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt

from chessdip.artists.piece import PieceArtist
from chessdip.artists.board import BoardArtist
from chessdip.core.order import *
from chessdip.artists.order import *

class VisualInterface:
    """
    The figure/axes of the game instance. Also makes artists.
    """
    def __init__(self):
        mpl.rcParams['toolbar'] = 'None'
        self.fig, self.ax = plt.subplots(1, 1, layout="tight")
        self.stale = False
    
    def set_stale(self, stale=True):
        self.stale = stale
    
    def ion(self):
        plt.ion()
    
    def ioff(self):
        plt.ioff()
    
    def show(self):
        plt.show()
    
    def render(self):
        if self.stale:
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            self.stale = False
    
    def make_piece_artist(self, piece):
        return PieceArtist(piece)
    
    def make_order_artist(self, order, supported_artist):
        if isinstance(order, HoldOrder):
            return HoldOrderArtist(order)
        elif isinstance(order, MoveOrder):
            return MoveOrderArtist(order)
        elif isinstance(order, ConvoyOrder):
            return ConvoyOrderArtist(order)
        elif isinstance(order, SupportHoldOrder):
            return SupportHoldOrderArtist(order, supported_artist)
        elif isinstance(order, SupportMoveOrder):
            return SupportMoveOrderArtist(order, supported_artist)
        elif isinstance(order, SupportConvoyOrder):
            return SupportConvoyOrderArtist(order, supported_artist)
        elif isinstance(order, SupportOrder):
            return SupportOrderArtist(order, supported_artist)
        elif isinstance(order, BuildOrder):
            return BuildOrderArtist(order)
        elif isinstance(order, DisbandOrder):
            return DisbandOrderArtist(order)
        else:
            raise ValueError(f"No artist for {order}!")
    
    def add_artist(self, artist):
        artist.add_to_ax(self.ax)
        self.stale = True