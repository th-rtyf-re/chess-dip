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
    SUPPORT = 6
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
    
    def __init__(self, piece, *other_args, visualizer=None, remove_method=None, virtual=False):
        self.piece = piece
        self.other_args = other_args
        self.visualizer = visualizer
        self._full_remove_method = remove_method
        self.virtual = virtual
        
        self.supports = []
        self.convoys = []
        self.supported_order = None
        self.convoyed_order = None
    
    def __str__(self):
        pass
    
    def get_args(self):
        return (self.piece,) + self.other_args
    
    def get_intermediate_squares(self):
        return []
    
    def is_inheritable(self, *args):
        return False
    
    def get_piece(self):
        return self.piece
    
    def execute(self, board, console):
        return False
    
    def set_virtual(self, virtual=True):
        self.virtual = virtual
        self.artist.set_virtual(virtual)
        for convoy_order in self.convoys:
            convoy_order.set_virtual(virtual)
    
    def add_support(self, support_order):
        self.supports.append(support_order)
        self.visualizer.add_support(self, support_order)
    
    def remove_support(self, support_order):
        self.supports.remove(support_order)
        self.artist.remove_support(support_order)
    
    def add_convoy(self, convoy_order):
        self.convoys.append(convoy_order)
    
    def remove_convoy(self, convoy_order):
        self.convoys.remove(convoy_order)
    
    def inherit_convoys(self, other_order):
        self.convoys = other_order.convoys
        for convoy in self.convoys:
            convoy.convoyed_order = self
            convoy.set_virtual(self.virtual)
    
class OrderArtist:
    def __init__(self, order):
        self.patches = []
        self.support_patches = {}
    
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
        pass
    
    def remove_support(self, support_order):
        for patch in self.support_patches[support_order]:
            patch.remove()
        del self.support_patches[support_order]

class HoldOrder(Order):
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.chess_path = ChessPath(piece, piece.square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} hold"
    
    def get_landing_square(self):
        return self.piece.square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        console.out(f"{self.piece} held.")
        return True

class HoldOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.radius = .4
        self.width = .1
        center = order.piece.square.file, order.piece.square.rank
        path0 = Path.circle(center, radius=self.radius - self.width / 2)
        path1 = Path.circle(center, radius=self.radius + self.width / 2)
        vertices1 = path1.vertices
        vertices1[:, 0] = 2 * center[0] - vertices1[:, 0]
        codes1 = path1.codes
        path = Path.make_compound_path(path0, Path(vertices1, codes1))
        linestyle = ":" if order.virtual else "-"
        patch = mpl.patches.PathPatch(path, fc=order.piece.power.square_color[0], ec="k", lw=1.5, ls=linestyle, joinstyle="round", capstyle="round")
        self.patches.append(patch)
    
    def set_virtual(self, virtual):
        linestyle = ":" if virtual else "-"
        for patch in self.patches:
            patch.set_linestyle(linestyle)
    
    def add_support(self, support_order):
        junction = support_order.artist.get_path_end()
        patch = mpl.patches.Circle(junction, radius=self.width, fc="w", ec="k", lw=1.5)
        self.support_patches[support_order] = [patch]
        return self.support_patches[support_order]

class MoveOrder(Order):
    def __init__(self, piece, landing_square, visualizer, remove_method, virtual=False):
        super().__init__(piece, landing_square, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.landing_square = landing_square
        self.chess_path = ChessPath(piece, self.landing_square)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} move to {self.landing_square}"
    
    def get_landing_square(self):
        return self.landing_square
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
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

class MoveOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.width = .1
        self.path = order.chess_path.artist.compute_path()
        arrow_style = mpl.patches.ArrowStyle("->", head_length=.2)
        arrow_paths, _ = arrow_style.transmute(self.path, mutation_size=1, linewidth=0)
        arrow_path = Path.make_compound_path(*arrow_paths)
        linestyle = ":" if order.virtual else "-"
        kwargs = dict(fc="none", ls=linestyle, joinstyle="round", capstyle="round")
        patch = mpl.patches.PathPatch(arrow_path, ec="k", lw=4, **kwargs)
        self.patches.append(patch)
        patch = mpl.patches.PathPatch(arrow_path, ec=order.piece.power.square_color[0], lw=2, **kwargs)
        self.patches.append(patch)
        self.junction = self._get_junction()
    
    def set_virtual(self, virtual):
        linestyle = ":" if virtual else "-"
        for patch in self.patches:
            patch.set_linestyle(linestyle)
    
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
        patch = mpl.patches.Circle(self.junction, radius=self.width, fc="w", ec="k", lw=1.5)
        self.support_patches[support_order] = [patch]
        return self.support_patches[support_order]

class ConvoyOrder(Order):
    def __init__(self, piece, square, convoyed_order, visualizer, remove_method, virtual=False):
        """
        piece should be None
        """
        super().__init__(piece, square, convoyed_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.square = square
        self.convoyed_order = convoyed_order
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.square} convoy {self.convoyed_order}"
    
    def get_landing_square(self):
        return self.square
    
    def execute(self, board, console):
        if self.square in self.convoyed_order.get_intermediate_squares():
            console.out(f"{self.square} convoyed {self.convoyed_order}.")
            return True
        console.out(f"{self.square} cannot support {self.convoyed_order}.")
        return False
    
    def update_convoyed_order(self, new_order):# because it can change!
        self.convoyed_order = new_order

class ConvoyOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.width = .1
    
    def set_virtual(self, virtual):
        linestyle = ":" if virtual else "-"
        for patch in self.patches:
            patch.set_linestyle(linestyle)
    
    def add_support(self, support_order):
        junction = support_order.artist.get_path_end()
        patch = mpl.patches.Circle(junction, radius=self.width, fc="w", ec="k", lw=1.5)
        self.support_patches[support_order] = [patch]
        return self.support_patches[support_order]

class SupportOrder(Order):
    def __init__(self, piece, supported_square, visualizer, remove_method, virtual=False):
        super().__init__(piece, supported_square, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_square = supported_square
        self.chess_path = ChessPath(piece, supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} generic support {self.supported_square}"
    
    def get_args(self):
        return (self.piece, self.supported_square)
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def is_inheritable(self, piece, supported_order):
        return piece == self.piece and supported_order.get_landing_square() == self.supported_square

class SupportOrderArtist(OrderArtist):
    def __init__(self, order):
        super().__init__(order)
        self.patch_kwargs = dict(fc="none", joinstyle="round", capstyle="round")
        if type(self) is SupportOrderArtist:
            self.patches = self.make_patches(order)
            self.set_virtual(order.virtual)
        
    def make_patches(self, order, **kwargs):
        patches = []
        path = order.chess_path.artist.compute_path(**kwargs)
        patch = mpl.patches.PathPatch(path, ec="k", lw=4, **self.patch_kwargs)
        patches.append(patch)
        patch = mpl.patches.PathPatch(path, ec="w", lw=2, **self.patch_kwargs)
        patches.append(patch)
        patch = mpl.patches.PathPatch(path, ec=order.piece.power.square_color[0], lw=1, **self.patch_kwargs)
        patches.append(patch)
        return patches

    def set_virtual(self, virtual):
        linestyle = (0, (1, 5)) if virtual else "-"
        for patch in self.patches:
            patch.set_linestyle(linestyle)
    
    def get_path_end(self):
        return self.patches[0].get_path().vertices[-1]

class SupportHoldOrder(SupportOrder):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportHoldOrderArtist(SupportOrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.patches = self.make_patches(order, shrink=order.supported_order.artist.radius)
        self.set_virtual(order.virtual)

class SupportMoveOrder(SupportOrder):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportMoveOrderArtist(SupportOrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.patches = self.make_patches(order, support=order.supported_order.artist.junction)
        self.set_virtual(order.virtual)

class SupportConvoyOrder(SupportOrder):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportConvoyOrderArtist(SupportOrderArtist):
    def __init__(self, order):
        super().__init__(order)
        
        self.patches = self.make_patches(order)
        self.set_virtual(order.virtual)

class BuildOrder(Order):
    def __init__(self, power, piece_code, square, visualizer, remove_method, virtual=False):
        super().__init__(None, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
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
        super().__init__(order)
        
        square = order.square
        rank, file = square.rank, square.file
        patch = mpl.patches.Circle((square.file, square.rank), radius=.45, fc="none", ec="k", ls=":", lw=1, capstyle="butt")
        piece = Piece(order.piece_code, order.power, order.square, order.visualizer)
        self.patches.append(patch)
        self.patches.extend(piece.artist.get_patches())

class DisbandOrder(Order):
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        return f"{self.piece} disband"
    
    def execute(self, board, console):
        board.remove_piece(self.piece)
        console.out(f"{self.piece} disbanded.")
        return True

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