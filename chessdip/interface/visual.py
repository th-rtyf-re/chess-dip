# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt

from chessdip.artists.piece import PieceArtist
from chessdip.artists.board import BoardArtist
from chessdip.core.order import (
    HoldOrder, MoveOrder, ConvoyOrder, SupportOrder,
    SupportHoldOrder, SupportMoveOrder, SupportConvoyOrder,
    BuildOrder, DisbandOrder
)
from chessdip.artists.order import (
    OrderArtist,
    HoldOrderArtist, MoveOrderArtist, ConvoyOrderArtist, SupportOrderArtist,
    SupportHoldOrderArtist, SupportMoveOrderArtist, SupportConvoyOrderArtist,
    BuildOrderArtist, DisbandOrderArtist
)

class LineDataUnits(mpl.lines.Line2D):
    """
    Class like Line2D except that the line width is specified in data units.
    Adapted from https://stackoverflow.com/a/42972469/17357015.
    """
    def __init__(self, *args, **kwargs):
        _lw_data = kwargs.pop("linewidth", 1) 
        super().__init__(*args, **kwargs)
        self._lw_data = _lw_data

    def _get_lw(self):
        if self.axes is not None:
            ppd = 72./self.axes.figure.dpi
            trans = self.axes.transData.transform
            return ((trans((1, self._lw_data))-trans((0, 0)))*ppd)[1]
        else:
            return 1

    def _set_lw(self, lw):
        self._lw_data = lw

    _linewidth = property(_get_lw, _set_lw)

from matplotlib import font_manager
font_path = "chessdip/interface/font/Figtree-Regular.otf" # Your font path goes here,
font_manager.fontManager.addfont(font_path)
prop = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.sans-serif'] = "Figtree"

class VisualInterface:
    """
    The figure/axes of the game instance. This class also creates the
    artists associated to various game objects.
    """
    def __init__(self):
        mpl.rcParams['toolbar'] = 'None'
        self.fig, self.ax = plt.subplots(1, 1, num="Chess Dip", figsize=(5, 5))
        margin = 0#.07
        self.fig.subplots_adjust(left=margin, bottom=margin, right=1 - margin, top=1 - margin)
        self.stale = False
        
        self.global_kwargs = dict(
            path_width=4,
            edge_width=1,
            piece_radius=.3,
            dot_radius=.1,
            support_patch_zorder=1.5
        )
    
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
    
    def set_title(self, title):
        self.ax.set_title(title)
        self.stale = True
    
    def make_board_artist(self, board):
        return BoardArtist(board, self.global_kwargs)
    
    def make_piece_artist(self, piece):
        return PieceArtist(piece, self.global_kwargs)
    
    def make_order_artist(self, order, supported_artist):
        if isinstance(order, HoldOrder):
            return HoldOrderArtist(order, self.global_kwargs)
        elif isinstance(order, MoveOrder):
            return MoveOrderArtist(order, self.global_kwargs)
        elif isinstance(order, ConvoyOrder):
            return ConvoyOrderArtist(order, self.global_kwargs)
        elif isinstance(order, SupportHoldOrder):
            return SupportHoldOrderArtist(order, supported_artist, self.global_kwargs)
        elif isinstance(order, SupportMoveOrder):
            return SupportMoveOrderArtist(order, supported_artist, self.global_kwargs)
        elif isinstance(order, SupportConvoyOrder):
            return SupportConvoyOrderArtist(order, supported_artist, self.global_kwargs)
        elif isinstance(order, SupportOrder):
            return SupportOrderArtist(order, supported_artist, self.global_kwargs)
        elif isinstance(order, BuildOrder):
            return BuildOrderArtist(order, self.global_kwargs)
        elif isinstance(order, DisbandOrder):
            return DisbandOrderArtist(order, self.global_kwargs)
        else:
            raise ValueError(f"No artist for {order}!")
    
    def add_artist(self, artist):
        artist.add_to_ax(self.ax, zorder=self._get_zorder(artist))
        self.stale = True
    
    def _get_zorder(self, artist):
        if isinstance(artist, BoardArtist):
            return 1.
        elif isinstance(artist, PieceArtist):
            return 1.1
        elif isinstance(artist, HoldOrderArtist):
            if not artist.get_virtual():
                return 1.2
            else:
                return 1.25
        elif isinstance(artist, OrderArtist):
            if not artist.get_virtual():
                return 1.3
            else:
                return 1.35
        else:
            return 1.