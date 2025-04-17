# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np

from piece import *
from chess_path import *

class Order:
    HOLD = 0
    MOVE = 1
    CONVOY = 2
    SUPPORT_HOLD = 3
    SUPPORT_MOVE = 4
    SUPPORT_CONVOY = 5
    BUILD = -1
    DISBAND = -2
    
    support_order_codes = {
        SUPPORT_HOLD: HOLD,
        SUPPORT_MOVE: MOVE,
        SUPPORT_CONVOY: CONVOY
    }
    
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        self.piece = piece
        self.visualizer = visualizer
        self._full_remove_method = remove_method
        self.virtual = virtual
        
        self.supports = []
        self.supported_order = None
    
    def __str__(self):
        pass
    
    def is_like(self, other):
        pass
    
    def get_piece(self):
        return self.piece
    
    def execute(self, board, console):
        return False
    
    def remove(self):
        if not self.virtual and self.supports:
            self.set_virtual(True)
        elif not self.supports: # full removal
            self._full_remove_method(self)
            if self.supported_order is not None:
                self.supported_order.supports.remove(self)
                self.supported_order.update()
    
    def update(self):
        if self.virtual and not self.supports:
            self.remove()
    
    def set_virtual(self, virtual):
        self.virtual = virtual
        self.artist.set_virtual(virtual)
    
    def add_support(self, support_order):
        self.supports.append(support_order)

class OrderArtist:
    def __init__(self, order):
        self.patches = []
    
    def add_to_ax(self, ax):
        for patch in self.patches:
            ax.add_artist(patch)

    def remove(self):
        for patch in self.patches:
            patch.remove()
    
    def set_virtual(self, virtual):
        pass

class HoldOrder(Order):
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer, remove_method, virtual)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} hold"
    
    def is_like(self, piece):
        return self.piece == piece
    
    def execute(self, board, console):
        if self.virtual:
            return False
        console.out(f"{self.piece} held.")
        return True

class HoldOrderArtist(OrderArtist):
    def __init__(self, order):
        self.radius = .4
        width = .1
        center = order.piece.square.file, order.piece.square.rank
        path0 = Path.circle(center, radius=self.radius - width / 2)
        path1 = Path.circle(center, radius=self.radius + width / 2)
        vertices1 = path1.vertices
        vertices1[:, 0] = 2 * center[0] - vertices1[:, 0]
        codes1 = path1.codes
        path = Path.make_compound_path(path0, Path(vertices1, codes1))
        linestyle = ":" if order.virtual else "-"
        patch = mpl.patches.PathPatch(path, fc=order.piece.power.square_color[0], ec="k", lw=1.5, ls=linestyle)
        self.patches = [patch]
    
    def set_virtual(self, virtual):
        linestyle = ":" if virtual else "-"
        for patch in self.patches:
            patch.set_linestyle(linestyle)
    
    def get_junction(self, support_order):
        pass

class MoveOrder(Order):
    def __init__(self, piece, landing_square, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer, remove_method, virtual)
        
        self.landing_square = landing_square
        self.chess_path = ChessPath(piece, self.landing_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        return f"{self.piece} move to {self.landing_square}"
    
    def is_like(self, piece, landing_square):
        return self.piece == piece and self.landing_square == landing_square
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot move to {self.landing_square}.")
            return False
        other_piece = board.get_piece(self.landing_square)
        if other_piece is not None:
            board.remove_piece(other_piece)
        board.move_piece_to(self.piece, self.landing_square)
        board.set_ownership(self.landing_square, self.piece.power)
        console.out(f"{self.piece} moved to {self.landing_square}.")
        return True

def move_path(start, end, width=.1, head_width=.3, alpha=45, shrink=0):
    x0, y0 = start
    x1, y1 = end
    vec = np.array([x1 - x0, y1 - y0], dtype=float)
    dist = np.linalg.norm(vec)
    direction = vec / dist
    
    # draw arrow going up
    ax, ay = 0, shrink
    bx, by = 0, dist - shrink
    w = width
    hw = head_width
    
    angle = np.deg2rad(alpha)
    r = w / 2
    hr = hw / 2
    hh = w / np.sin(angle)# head height
    z = by - hh
    
    left_vertices = [
        (-r, ay),
        (-r, z - r / np.tan(angle)),
        (-hw / 2, z - hr / np.tan(angle)),
        (-hw / 2, by - hr / np.tan(angle)),
    ]
    right_vertices = [(-x, y) for x, y in left_vertices[::-1]]
    vertices = np.array(left_vertices + [(ax, by)] + right_vertices + [(- r, ay)])
    rot = np.array([[direction[1], direction[0]], [-direction[0], direction[1]]])
    v0 = np.array([x0, y0])
    for i in range(len(vertices)):
        vertices[i] = v0 + rot @ vertices[i]
    codes = [Path.MOVETO] + (len(vertices) - 2) * [Path.LINETO] + [Path.CLOSEPOLY]
    path = Path(vertices, codes)
    return path

class MoveOrderArtist(OrderArtist):
    def __init__(self, order):
        path = order.chess_path.artist.compute_path()
        arrow_style = mpl.patches.ArrowStyle("->", head_length=.2)
        arrow_paths, _ = arrow_style.transmute(path, mutation_size=1, linewidth=0)
        arrow_path = Path.make_compound_path(*arrow_paths)
        kwargs = dict(fc="none", joinstyle="round", capstyle="round")
        self.patches = []
        patch = mpl.patches.PathPatch(arrow_path, ec="k", lw=4, **kwargs)
        self.patches.append(patch)
        patch = mpl.patches.PathPatch(arrow_path, ec=order.piece.power.square_color[0], lw=2, **kwargs)
        self.patches.append(patch)

class SupportHoldOrder(Order):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer, remove_method, virtual)
        
        self.supported_order = supported_order
        self.supported_order.add_support(self)
        
        self.chess_path = ChessPath(piece, supported_order.piece.square)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        return f"{self.piece} support {self.supported_order}"
    
    def is_like(self, piece, supported_order):
        return self.piece == piece and self.supported_order == supported_order
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportHoldOrderArtist(OrderArtist):
    def __init__(self, order):
        # junction = order.supported_order.artist.get_junction(order)
        path = order.chess_path.artist.compute_path(shrink=order.supported_order.artist.radius)
        kwargs = dict(fc="none", joinstyle="round", capstyle="round")
        self.patches = []
        patch = mpl.patches.PathPatch(path, ec="k", lw=4, **kwargs)
        self.patches.append(patch)
        patch = mpl.patches.PathPatch(path, ec=order.piece.power.square_color[0], lw=2, **kwargs)
        self.patches.append(patch)

class BuildOrder(Order):
    def __init__(self, power, piece_code, square, visualizer, remove_method, virtual=False):
        super().__init__(None, visualizer, remove_method, virtual)
        self.power = power
        self.piece_code = piece_code
        self.square = square
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        names = ["Pawn", "Knight", "Bishop", "Rook", "King"]
        return f"{self.power} build {names[self.piece_code]} on {self.square}"
    
    def execute(self, board, console):
        board.vacate_square(self.square)
        piece = board.add_piece(self.piece_code, self.power, self.square)
        console.out(f"{self.power} built {piece}.")
        return piece

class BuildOrderArtist(OrderArtist):
    def __init__(self, order):
        square = order.square
        rank, file = square.rank, square.file
        patch = mpl.patches.Circle((square.file, square.rank), radius=.45, fc="none", ec="k", ls=":", lw=1, capstyle="butt")
        piece = Piece(order.piece_code, order.power, order.square, order.visualizer)
        self.patches = [patch] + piece.artist.get_patches()

class DisbandOrder(Order):
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer, remove_method, virtual)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        return f"{self.piece} disband"
    
    def execute(self, board, console):
        board.remove_piece(self.piece)
        console.out(f"{self.piece} disbanded.")
        return True

class DisbandOrderArtist(OrderArtist):
    def __init__(self, order):
        self.patches = []
        square = order.piece.square
        rank, file = square.rank, square.file
        w = .45
        x0, x1 = square.file - w, square.file + w
        y0, y1 = square.rank - w, square.rank + w
        path = Path([(x0, y0), (x1, y1), (x0, y1), (x1, y0)], [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO])
        patch = mpl.patches.PathPatch(path, fc="none", ec="r", linewidth=4, capstyle="round")
        self.patches.append(patch)