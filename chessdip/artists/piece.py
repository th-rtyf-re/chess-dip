# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from chessdip.board.piece import Piece

class PiecePath:
    """
    Namespace for the paths that define piece sprites. All piece sprites
    are drawn using Matplotlib PathPatches.
    """
    def pawn_path():
        path = Path.circle(radius=1) # Approximate circle
        return path

    def king_path():
        alpha = 15
        arc_path = Path.arc(180 - alpha, alpha)
        y = arc_path.vertices[0, 1]
        cross_vertices = [
            (0, y),
            (0, 1),
            (-(1 - y) / 2, (1 + y) / 2),
            ((1 - y) / 2, (1 + y) / 2)
        ]
        
        vertices = np.append(arc_path.vertices, [arc_path.vertices[0]] + cross_vertices, axis=0)
        codes = np.append(arc_path.codes, [Path.CLOSEPOLY, Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO])
        path = Path(vertices, codes)
        return path

    def rook_path():
        """
        The battlement is specified as follows:
                    x
                <------->
          v     w     v
        <---> <---> <--->
         ___   ___   ___
        |   |_|   |_|   | z
        
                  <->
                   z
        
        The path goes from right to left.
        """
        alpha = 45
        arc_path = Path.arc(180 - alpha, alpha)
        x, y = arc_path.vertices[-1]
        z = .3 # gap height and width
        w = x * .5 # middle merlon width
        v = (2 * x - 2 * z - w) / 2 # side merlon width
        battlement_vertices = [
            (x - v, y),
            (x - v, y - z),
            (x - v - z, y - z),
            (x - v - z, y),
            (x - v - z - w, y),
            (x - v - z - w, y - z),
            (x - v - 2*z - w, y - z),
            (x - v - 2*z - w, y),
            (-x, y)
        ]
        battlement_codes = (len(battlement_vertices) - 1) * [Path.LINETO] + [Path.CLOSEPOLY]
        vertices = np.append(arc_path.vertices, battlement_vertices, axis=0)
        codes = np.append(arc_path.codes, battlement_codes)
        path = Path(vertices, codes)
        return path

    def _get_miter_angle(x, y, alpha):
        """
        Consider the unit circle centered at the origin, O. Consider a ray
        starting at (x, y) with angle alpha relative to the x-axis. This ray
        intersect the circle at a point P. Then the miter angle, beta, is
        the angle at O between the x-axis and the point P:
        
                     P
                    ,|
                  ., |
                . ,  |
           ___.__,a__'
          | .    |   |
          |b_____|   | y
          O
          <------>
             x
        
        The comma and dot lines form angles a(lpha) and b(eta), respectively,
        with the x-axis. The angles are separated by a vector (x, y). The
        dot line is of length 1. To compute b, we use the fact that
        
            tan(a) = (sin(b) - y) / (cos(b) - x)
        """
        tan_alpha = np.tan(np.deg2rad(alpha))
        a = y - tan_alpha - x * tan_alpha
        b = -2
        c = y + tan_alpha - x * tan_alpha
        t = (-b - np.sqrt(b * b - 4 * a * c)) / (2 * a)
        beta = 2 * np.rad2deg(np.arctan(t))
        return beta

    def bishop_path():
        alpha = 60
        x1, y1 = .2, -.2
        x0, y0 = x1 - .4, y1
        
        theta0 = PiecePath._get_miter_angle(x0, y0, alpha)
        theta1 = PiecePath._get_miter_angle(x1, y1, alpha)
        
        arc_path = Path.arc(theta0, theta1)
        slit_vertices = [(x1, y1), (x0, y0), arc_path.vertices[0]]
        slit_codes = [Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
        vertices = np.append(arc_path.vertices, slit_vertices, axis=0)
        codes = np.append(arc_path.codes, slit_codes)
        path = Path(vertices, codes)
        return path

    def knight_path():
        nose = (-1, 0)
        chin = (-.8, -.2)
        jaw = (.2, .05)
        neck_angle = -110
        ear_angle = 110
        
        arc_path = Path.arc(neck_angle, ear_angle)
        snout_vertices = [nose, chin, jaw]
        vertices = np.concatenate(([(0, 0)], arc_path.vertices, snout_vertices), axis=0)
        codes = np.concatenate(([Path.MOVETO, Path.LINETO], arc_path.codes[1:], len(snout_vertices) * [Path.LINETO]))
        path = Path(vertices, codes)
        return path

class PieceArtist:
    """
    Artist for pieces. This class has one class attribute, `piece_path_dict`,
    which to each piece code associates the sprite path as described by
    PiecePath.
    
    Pieces are drawn with three patches: a main patch with a face color, an
    edge path that draws a black edge for the piece, and a shadow patch.
    """
    piece_path_dict = {
        Piece.PAWN: PiecePath.pawn_path(),
        Piece.KNIGHT: PiecePath.knight_path(),
        Piece.BISHOP: PiecePath.bishop_path(),
        Piece.ROOK: PiecePath.rook_path(),
        Piece.KING: PiecePath.king_path()
    }
    
    def __init__(self, piece, global_kwargs):
        """
        Parameters:
        ----------
        - piece: Piece.
        - global_kwargs: dict. Keyword arguments for various lengths.
        """
        self.piece = piece
        self.ax = None
    
        self.kwargs = dict(lw=2 * global_kwargs["edge_width"], capstyle="butt", joinstyle="round")
        self.r = global_kwargs["piece_radius"]
        self.piece_radius = {
            Piece.PAWN: 2 / 3 * self.r,
            Piece.KNIGHT: self.r,
            Piece.BISHOP: self.r,
            Piece.ROOK: self.r,
            Piece.KING: self.r
        }
        
        self.square = self.piece.square
        self.fc, self.highlight = self.piece.power.piece_color
        
        self.shift = {
            Piece.PAWN: (-.06, -.02),
            Piece.KNIGHT: (-.06, -.02),
            Piece.BISHOP: (-.06, 0.),
            Piece.ROOK: (-.04, -.0),
            Piece.KING: (-.08, -.02)
        }
        
        self.path = PieceArtist.piece_path_dict[piece.code]
        
        self.affine_transform = mpl.transforms.Affine2D().translate(self.square.file, self.square.rank)
        self.scale_transform = mpl.transforms.Affine2D().scale(self.piece_radius[self.piece.code])
        self.transform = self.scale_transform + self.affine_transform
        self.shadow_transform = self.scale_transform + mpl.transforms.Affine2D().translate(*self.shift[self.piece.code]) + self.affine_transform
        
    
    def __str__(self):
        return f"PieceArtist({self.piece})"
    
    def _make_patches(self, zorder=1.):
        piece_patch = mpl.patches.PathPatch(self.path, fc=self.highlight, ec="none", transform=self.transform + self.ax.transData, **self.kwargs, zorder=zorder)
        
        shadow_patch = mpl.patches.PathPatch(self.path, fc=self.fc, ec=self.highlight, transform=self.shadow_transform + self.ax.transData, **self.kwargs, zorder=zorder)
        shadow_patch.set_clip_path(piece_patch)
        
        outline_patch = mpl.patches.PathPatch(self.path, fc="none", ec="k", transform=self.transform + self.ax.transData, **self.kwargs, zorder=zorder)
        return [piece_patch, shadow_patch, outline_patch]
    
    def _add_special_patches(self, zorder=1.):
        if self.piece.code == Piece.KNIGHT:
            x, y, r = -.15, .5, self.r / 2
            self.patches.append(mpl.patches.Circle((x, y), radius=r, fc="k", ec="none", transform=self.transform + self.ax.transData, **self.kwargs, zorder=zorder))
    
    def get_patches(self):
        return self.patches
    
    def add_to_ax(self, ax, zorder=1.):
        self.ax = ax
        self.patches = self._make_patches(zorder=zorder)
        self._add_special_patches(zorder=zorder)
        
        for patch in self.patches:
            ax.add_patch(patch)
    
    def move_to(self, square):
        self.affine_transform.translate(square.file - self.square.file, square.rank - self.square.rank)
        self.square = square
    
    def remove(self):
        for patch in self.patches:
            patch.remove()