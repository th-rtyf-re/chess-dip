# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from chessdip.board.piece import Piece
from chessdip.artists.piece import PieceArtist
from chessdip.artists.chess_path import ChessPathArtist

class OrderArtist:
    def __init__(self, order):
        self.order = order
        self.ax = None
        self.supported_artist = None
        self.patches = []
        self.support_patches = {}
        self.children_artists = []
        self.patch_kwargs = dict(fc="none", joinstyle="round", capstyle="projecting")
        self.support_kwargs = dict(radius=.1, fc="w", ec="k", lw=1.5, zorder=1.5)
    
    def _add_patches(self, patches):
        if self.ax is not None:
            for patch in patches:
                self.ax.add_patch(patch)
    
    def add_to_ax(self, ax):
        self.ax = ax
        for patch in self.patches:
            self.ax.add_patch(patch)
        for patches in self.support_patches.values():
            for patch in patches:
                self.ax.add_patch(patch)
        for artist in self.children_artists:
            artist.add_to_ax(self.ax)
    
    def remove(self):
        for patch in self.patches:
            patch.remove()
        for patches in self.support_patches.values():
            for patch in patches:
                patch.remove()
    
    def remove_support(self, support_artist):
        for patch in self.support_patches[support_artist]:
            patch.remove()
        del self.support_patches[support_artist]
    
    def add_support(self, support_artist):
        junction = self._get_support_junction(support_artist)
        patch = mpl.patches.Circle(junction, **self.support_kwargs)
        self.support_patches[support_artist] = [patch]
        self._add_patches(self.support_patches[support_artist])
    
    def _get_support_junction(self, support_artist):
        pass

    def make_path_patches(self, path, n=None):
        self.ecs = ["k", self.order.piece.power.square_color[0], "w"]
        self.lws = [4, 2, .5]
        self.virtual_lss = [(0, (3 / lw, 5 / lw)) for lw in self.lws]
        
        if n is None:
            n = len(self.ecs)
        for ec, lw, _ in zip(self.ecs, self.lws, range(n)):
            patch = mpl.patches.PathPatch(path, ec=ec, lw=lw, **self.patch_kwargs)
            self.patches.append(patch)
    
    def set_virtual(self, virtual):
        linestyles = self.virtual_lss if virtual else ["-"] * len(self.patches)
        for patch, ls in zip(self.patches, linestyles):
            patch.set_linestyle(ls)

class HoldOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.radius = .4
        center = order.piece.square.file, order.piece.square.rank
        path = Path.circle(center, radius=self.radius)
        self.make_path_patches(path, 2)
        self.set_virtual(order.virtual)
    
    def _get_support_junction(self, support_artist):
        return support_artist.get_path_end()

class MoveOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.path = ChessPathArtist(order.chess_path).compute_path()
        arrow_style = mpl.patches.ArrowStyle("->", head_length=.2)
        arrow_paths, _ = arrow_style.transmute(self.path, mutation_size=1, linewidth=0)
        arrow_path = Path.make_compound_path(*arrow_paths)
        self.make_path_patches(arrow_path, 2)
        self.set_virtual(order.virtual)
        self.junction = self._get_junction()
    
    def _get_junction(self):
        """
        Get intersection between path and the edge of the landing square
        """
        v0, v1 = self.path.vertices[-2:]
        direction = v1 - v0
        norm = np.max(np.abs(direction))
        if norm != 0:
            direction = direction / norm
        junction = v1 - direction * 0.5
        return junction
    
    def _get_support_junction(self, support_artist):
        return self.junction

class ConvoyOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
    
    def set_virtual(self, virtual):
        return
    
    def _get_support_junction(self, support_artist):
        return support_artist.get_path_end()

class SupportOrderArtist(OrderArtist):
    def __init__(self, order, supported_artist):
        super().__init__(order)
        self.supported_artist = supported_artist
                
        if type(self) is SupportOrderArtist:
            path = ChessPathArtist(order.chess_path).compute_path()
            self.make_path_patches(path)
            self.set_virtual(order.virtual)
        
    def get_path_end(self):
        return self.patches[0].get_path().vertices[-1]

class SupportHoldOrderArtist(SupportOrderArtist):
    def __init__(self, order, supported_artist):
        super().__init__(order, supported_artist)
        
        path = ChessPathArtist(order.chess_path).compute_path(shrink=self.supported_artist.radius)
        self.make_path_patches(path)
        self.set_virtual(order.virtual)

class SupportMoveOrderArtist(SupportOrderArtist):
    def __init__(self, order, supported_artist):
        super().__init__(order, supported_artist)
        
        junction = self.supported_artist._get_support_junction(self)
        path = ChessPathArtist(order.chess_path).compute_path(junction=junction)
        self.make_path_patches(path)
        self.set_virtual(order.virtual)

class SupportConvoyOrderArtist(SupportOrderArtist):
    def __init__(self, order, supported_artist):
        super().__init__(order, supported_artist)
        
        path = ChessPathArtist(order.chess_path).compute_path()
        self.make_path_patches(path)
        self.set_virtual(order.virtual)

class BuildOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        square = order.square
        rank, file = square.rank, square.file
        patch = mpl.patches.Circle((square.file, square.rank), radius=.45, fc="none", ec="k", ls=":", lw=1, capstyle="butt")
        piece = Piece(order.piece_code, order.power, order.square)
        piece_artist = PieceArtist(piece)
        self.patches.append(patch)
        self.children_artists.append(piece_artist)

class DisbandOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        square = order.piece.square
        rank, file = square.rank, square.file
        w = .45
        x0, x1 = square.file - w, square.file + w
        y0, y1 = square.rank - w, square.rank + w
        path = Path([(x0, y0), (x1, y1), (x0, y1), (x1, y0)], [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO])
        patch = mpl.patches.PathPatch(path, fc="none", ec="r", linewidth=4, capstyle="butt")
        self.patches.append(patch)