# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from chessdip.board.piece import Piece
from chessdip.artists.piece import PieceArtist
from chessdip.artists.chess_path import ChessPathArtist, ChessPathVector

class OrderArtist:
    def __init__(self, order, global_kwargs):
        self.order = order
        self.virtual = False
        self.ax = None
        self.supported_artist = None
        self.patches = []
        self.support_patches = {}
        self.children_artists = []
        self.patch_kwargs = dict(fc="none", joinstyle="miter", capstyle="round")
        self.support_kwargs = dict(radius=global_kwargs["dot_radius"], fc="w", ec="k", lw=1.5 * global_kwargs["edge_width"], zorder=1.5)
        lw0 = global_kwargs["path_width"] + global_kwargs["edge_width"]
        lw1 = global_kwargs["path_width"] - global_kwargs["edge_width"]
        self.lws = [lw0, lw1, lw1 / 3]
        dash_on = self.lws[0]
        dash_off = 1.5 * dash_on
        self.virtual_lss = [(0, (dash_on / lw, dash_off / lw)) for lw in self.lws]
        self.global_shrink = 2 * global_kwargs["dot_radius"]
        self.hold_radius = .4
        self.shrinkA = .3
    
    def _add_patches(self, patches):
        if self.ax is not None:
            for patch in patches:
                self.ax.add_patch(patch)
    
    def add_to_ax(self, ax, zorder=1.):
        self.ax = ax
        for patch in self.patches:
            patch.set_zorder(zorder)
            self.ax.add_patch(patch)
        for patches in self.support_patches.values():
            for patch in patches:
                self.ax.add_patch(patch)
        for artist in self.children_artists:
            artist.add_to_ax(self.ax, zorder=zorder)
    
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
        junction = support_artist.get_path_end()
        patch = mpl.patches.Circle(junction, **self.support_kwargs)
        self.support_patches[support_artist] = [patch]
        self._add_patches(self.support_patches[support_artist])
    
    def _get_support_junction(self, support_artist):
        pass

    def make_path_patches(self, path, path_type=None):
        if path_type is None:
            path_type = "move"
        
        ecs = ["k", self.order.piece.power.path_color]
        if path_type == "support":
            ecs.append("w")
        elif path_type == "attack":
            ecs.append("k")
        
        for ec, lw in zip(ecs, self.lws):
            patch = mpl.patches.PathPatch(path, ec=ec, lw=lw, **self.patch_kwargs)
            self.patches.append(patch)
    
    # def update_path(self, path):
    #     for patch in self.patches:
    #         patch.set_path(path)
    #     # do something for support patches as well...
    
    def update_vertices(self, vertices):
        path = Path(vertices, [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 1))
        for patch in self.patches:
            patch.set_path(path)
        # do something for support patches as well...
    
    def update_support_patch(self, support_artist):
        for patch in self.support_patches[support_artist]:
            patch.remove()
        self.support_patches[support_artist].clear()
        self.add_support(support_artist)
    
    def get_virtual(self):
        return self.virtual
    
    def set_virtual(self, virtual):
        self.virtual = virtual
        linestyles = self.virtual_lss if virtual else ["-"] * len(self.patches)
        for patch, ls in zip(self.patches, linestyles):
            patch.set_linestyle(ls)
    
    def set_success(self, success):
        if self.patches:
            self.patches[0].set_ec("k" if success else "r")
    
    def set_support_success(self, support_artist, success):
        try:
            for patch in self.support_patches[support_artist]:
                patch.set_ec("k" if success else "r")
        except:
            pass

class HoldOrderArtist(OrderArtist):
    def __init__(self, order, global_kwargs):
        super().__init__(order, global_kwargs)
        
        center = order.piece.square.file, order.piece.square.rank
        path = Path.circle(center, radius=self.hold_radius)
        self.make_path_patches(path)
        self.set_virtual(order.virtual)
    
    def _get_support_junction(self, support_artist):
        return support_artist.get_path_end()

class MoveOrderArtist(OrderArtist):
    def __init__(self, order, global_kwargs):
        super().__init__(order, global_kwargs)
        
        self.path_artist = ChessPathArtist(self.order.chess_path, shrinkA=self.shrinkA, shrinkB=self.global_shrink)
        self.path = self.path_artist.compute_path()
        arrow_style = mpl.patches.ArrowStyle("->", head_width=.2, head_length=.2)
        arrow_paths, _ = arrow_style.transmute(self.path, mutation_size=1, linewidth=0)
        arrow_path = Path.make_compound_path(*arrow_paths)
        self.make_path_patches(arrow_path, path_type="attack" if order.is_attack() else "move")
        self.set_virtual(self.order.virtual)
        self.junction = self._get_junction()
    
    def _get_junction(self):
        """
        Get intersection between path and the edge of the landing square
        
        Adapted from https://stackoverflow.com/a/58055928/17357015
        """
        v0, v1 = self.path.vertices[-2:]
        square = self.order.get_landing_square()
        x0, x1 = square.file - .5, square.file + .5
        y0, y1 = square.rank - .5, square.rank + .5
        dx = v1[0] - v0[0]
        dy = v1[1] - v0[1]
        
        ex = x0 if dx > 0 else x1
        ey = y0 if dy > 0 else y1
        
        if dx == 0:
            return (v0[0], ey)
        elif dy == 0:
            return (ex, v0[1])
        else:
            tx = (ex - v0[0]) / dx
            ty = (ey - v0[1]) / dy
            if tx <= ty:
                y = v0[1] + tx * dy
                y = int(y + 1.) - .5 # cancel floating point errors
                return (ex, y)
            else:
                x = v0[0] + ty * dx
                x = int(x + 1.) - .5 # cancel floating point errors
                return (x, ey)
    
    def _get_support_junction(self, support_artist):
        return self._get_junction()
    
    def get_support_vector(self):
        """
        Vector with which support paths can intersect
        """
        pass
    
    def update_vertices(self, vertices):
        path = Path(vertices, [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 1))
        arrow_style = mpl.patches.ArrowStyle("->", head_width=.2, head_length=.2)
        arrow_paths, _ = arrow_style.transmute(path, mutation_size=1, linewidth=0)
        arrow_path = Path.make_compound_path(*arrow_paths)
        for patch in self.patches:
            patch.set_path(arrow_path)
        # do something for support patches as well...

class ConvoyOrderArtist(OrderArtist):
    def __init__(self, order, global_kwargs):
        super().__init__(order, global_kwargs)
    
    def set_virtual(self, virtual):
        return
    
    def _get_support_junction(self, support_artist):
        return support_artist.get_path_end()
    
    def get_support_vector(self):
        pass

class SupportOrderArtist(OrderArtist):
    def __init__(self, order, supported_artist, global_kwargs):
        super().__init__(order, global_kwargs)
        self.supported_artist = supported_artist
                
        if type(self) is SupportOrderArtist:
            self.path_artist = ChessPathArtist(self.order.chess_path)
            path = self.path_artist.compute_path()
            self.make_path_patches(path, path_type="support")
            self.set_virtual(order.virtual)
        
    def get_path_end(self):
        return self.patches[0].get_path().vertices[-1]

class SupportHoldOrderArtist(SupportOrderArtist):
    def __init__(self, order, supported_artist, global_kwargs):
        super().__init__(order, supported_artist, global_kwargs)
        
        self.path_artist = ChessPathArtist(self.order.chess_path, shrinkA=self.shrinkA, shrinkB=self.supported_artist.hold_radius)
        path = self.path_artist.compute_path()
        self.make_path_patches(path, path_type="support")
        self.set_virtual(order.virtual)

class SupportMoveOrderArtist(SupportOrderArtist):
    def __init__(self, order, supported_artist, global_kwargs):
        super().__init__(order, supported_artist, global_kwargs)
        
        junction = self.supported_artist._get_support_junction(self)
        self.path_artist = ChessPathArtist(self.order.chess_path, shrinkA=self.shrinkA, junction=junction)
        path = self.path_artist.compute_path()
        self.make_path_patches(path, path_type="support")
        self.set_virtual(order.virtual)

class SupportConvoyOrderArtist(SupportOrderArtist):
    def __init__(self, order, supported_artist, global_kwargs):
        super().__init__(order, supported_artist, global_kwargs)
        
        # junction = (self.order.get_landing_square().file, self.order.get_landing_square().rank)
        # self.path_artist = ChessPathArtist(self.order.chess_path, shrinkA=self.shrinkA, junction=junction)
        self.path_artist = ChessPathArtist(self.order.chess_path, shrinkA=self.shrinkA)
        path = self.path_artist.compute_path()
        self.make_path_patches(path, path_type="support")
        self.set_virtual(order.virtual)

class BuildOrderArtist(OrderArtist):
    def __init__(self, order, global_kwargs):
        super().__init__(order, global_kwargs)
        
        square = order.square
        rank, file = square.rank, square.file
        patch = mpl.patches.Circle((square.file, square.rank), radius=.45, fc="none", ec="k", ls=":", lw=1, capstyle="butt")
        piece = Piece(order.piece_code, order.power, order.square)
        piece_artist = PieceArtist(piece, global_kwargs)
        self.patches.append(patch)
        self.children_artists.append(piece_artist)

class DisbandOrderArtist(OrderArtist):
    def __init__(self, order, global_kwargs):
        super().__init__(order, global_kwargs)
        
        square = order.piece.square
        rank, file = square.rank, square.file
        w = .45
        x0, x1 = square.file - w, square.file + w
        y0, y1 = square.rank - w, square.rank + w
        path = Path([(x0, y0), (x1, y1), (x0, y1), (x1, y0)], [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO])
        patch = mpl.patches.PathPatch(path, fc="none", ec="r", linewidth=global_kwargs["path_width"], capstyle="butt")
        self.patches.append(patch)