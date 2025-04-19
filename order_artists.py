# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np

from piece import *
from chess_path import *
    
class OrderArtist:
    def __init__(self, order):
        self.patches = []
        self.support_patches = {}
        
        self.patch_kwargs = dict(fc="none", joinstyle="round", capstyle="projecting")
        self.ecs = ["k", order.piece.power.square_color[0], "w"]
        self.lws = [4, 2, .5]
        self.virtual_lss = [(0, (3 / lw, 5 / lw)) for lw in self.lws]
        
        self.support_kwargs = dict(radius=.1, fc="w", ec="k", lw=1.5, zorder=1.5)
    
    def make_patches(self, path, n=None):
        if n is None:
            n = len(self.ecs)
        for ec, lw, _ in zip(self.ecs, self.lws, range(n)):
            patch = mpl.patches.PathPatch(path, ec=ec, lw=lw, **self.patch_kwargs)
            self.patches.append(patch)
    
    def add_to_ax(self, ax):
        for patch in self.patches:
            ax.add_patch(patch)
        for patches in self.support_patches.values():
            for patch in patches:
                ax.add_patch(patch)

    def remove(self):
        for patch in self.patches:
            patch.remove()
        for patches in self.support_patches.values():
            for patch in patches:
                patch.remove()
    
    def set_virtual(self, virtual):
        linestyles = self.virtual_lss if virtual else ["-"] * len(self.patches)
        for patch, ls in zip(self.patches, linestyles):
            patch.set_linestyle(ls)
    
    def remove_support(self, support_order):
        for patch in self.support_patches[support_order]:
            patch.remove()
        del self.support_patches[support_order]

class HoldOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.radius = .4
        center = order.piece.square.file, order.piece.square.rank
        path = Path.circle(center, radius=self.radius)
        self.make_patches(path, 2)
        self.set_virtual(order.virtual)
    
    def add_support(self, support_order):
        junction = support_order.artist.get_path_end()
        patch = mpl.patches.Circle(junction, **self.support_kwargs)
        self.support_patches[support_order] = [patch]
        return self.support_patches[support_order]

class MoveOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.path = order.chess_path.artist.compute_path()
        arrow_style = mpl.patches.ArrowStyle("->", head_length=.2)
        arrow_paths, _ = arrow_style.transmute(self.path, mutation_size=1, linewidth=0)
        arrow_path = Path.make_compound_path(*arrow_paths)
        self.make_patches(arrow_path, 2)
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
    
    def add_support(self, support_order):
        patch = mpl.patches.Circle(self.junction, **self.support_kwargs)
        self.support_patches[support_order] = [patch]
        return self.support_patches[support_order]

class ConvoyOrderArtist(OrderArtist):
    def __init__(self, order):
        self.patches = []
        self.support_patches = {}
        
        self.support_kwargs = dict(radius=.1, fc="w", ec="k", lw=1.5, zorder=1.5)
    
    def set_virtual(self, virtual):
        return
    
    def add_support(self, support_order):
        junction = support_order.artist.get_path_end()
        patch = mpl.patches.Circle(junction, **self.support_kwargs)
        self.support_patches[support_order] = [patch]
        return self.support_patches[support_order]

class SupportOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
                
        if type(self) is SupportOrderArtist:
            path = order.chess_path.artist.compute_path()
            self.make_patches(path)
            self.set_virtual(order.virtual)
        
    def get_path_end(self):
        return self.patches[0].get_path().vertices[-1]

class SupportHoldOrderArtist(SupportOrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        path = order.chess_path.artist.compute_path(shrink=order.supported_order.artist.radius)
        self.make_patches(path)
        self.set_virtual(order.virtual)

class SupportMoveOrderArtist(SupportOrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        path = order.chess_path.artist.compute_path(support=order.supported_order.artist.junction)
        self.make_patches(path)
        self.set_virtual(order.virtual)

class SupportConvoyOrderArtist(SupportOrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        path = order.chess_path.artist.compute_path()
        self.make_patches(path)
        self.set_virtual(order.virtual)

class BuildOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        square = order.square
        rank, file = square.rank, square.file
        patch = mpl.patches.Circle((square.file, square.rank), radius=.45, fc="none", ec="k", ls=":", lw=1, capstyle="butt")
        piece = Piece(order.piece_code, order.power, order.square, order.visualizer)
        self.patches.append(patch)
        self.patches.extend(piece.artist.get_patches())

class DisbandOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        square = order.piece.square
        rank, file = square.rank, square.file
        w = .45
        x0, x1 = square.file - w, square.file + w
        y0, y1 = square.rank - w, square.rank + w
        path = Path([(x0, y0), (x1, y1), (x0, y1), (x1, y0)], [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO])
        patch = mpl.patches.PathPatch(path, fc="none", ec="r", linewidth=4, capstyle="round")
        self.patches.append(patch)