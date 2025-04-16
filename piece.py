# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

class Piece:
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    KING = 4
    
    piece_dict = {
        'P': PAWN,
        'N': KNIGHT,
        'B': BISHOP,
        'R': ROOK,
        'K': KING
    }
    
    def __init__(self, code, power, square, visualizer):
        self.code = code
        self.power = power
        self.square = square
        self.visualizer = visualizer
        
        self.artist = self.visualizer.make_piece_artist(self)
    
    def __str__(self):
        names = ["Pawn", "Knight", "Bishop", "Rook", "King"]
        return f"{self.power} {names[self.code]} at {self.square}"
    
    def move_to(self, square):
        self.visualizer.move_piece(self, square)
        self.square = square
    
    def remove(self):
        self.visualizer.erase_piece(self)

class PiecePath:
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
        The miter angle is specified as follows:
        
                    ,|
                  ., |
                . ,  |
           ___.__,a__'
          | .    |   |
          |b_____|   | y
        
          <------>
             x
        
        The comma and dot lines form angles a and b, respectively, with the
        horizontal axis. The angles are separated by a vector (x, y). The
        dot line is of length 1. Given a, compute b. We use the fact that
        
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
    piece_path_dict = {
        Piece.PAWN: PiecePath.pawn_path(),
        Piece.KNIGHT: PiecePath.knight_path(),
        Piece.BISHOP: PiecePath.bishop_path(),
        Piece.ROOK: PiecePath.rook_path(),
        Piece.KING: PiecePath.king_path()
    }
    
    def __init__(self, visualizer, piece):
        self.piece = piece
        
        self.square = self.piece.square
        self.fc, self.highlight = self.piece.power.piece_color
        self.kwargs = visualizer.piece_kwargs
        
        self.shift = (-.08, -.02)
        self.path = PieceArtist.piece_path_dict[piece.code]
        
        self.affine_transform = mpl.transforms.Affine2D().translate(self.square.file, self.square.rank)
        self.scale_transform = mpl.transforms.Affine2D().scale(visualizer.piece_radius[self.piece.code])
        self.transform = self.scale_transform + self.affine_transform + visualizer.ax.transData
        self.unshadow_transform = self.scale_transform + mpl.transforms.Affine2D().translate(*self.shift) + self.affine_transform + visualizer.ax.transData
        
        self.patches = self._make_patches()
        self._add_special_patches()
    
    def __str__(self):
        return f"PieceArtist({self.piece})"
    
    def _make_patches(self):
        piece_patch = mpl.patches.PathPatch(self.path, fc=self.highlight, ec="none", transform=self.transform, **self.kwargs)
        
        unshadow_patch = mpl.patches.PathPatch(self.path, fc=self.fc, ec=self.highlight, transform=self.unshadow_transform, **self.kwargs)
        unshadow_patch.set_clip_path(piece_patch)
        
        outline_patch = mpl.patches.PathPatch(self.path, fc="none", ec="k", transform=self.transform, **self.kwargs)
        return [piece_patch, unshadow_patch, outline_patch]
    
    def _add_special_patches(self):
        if self.piece.code == Piece.KNIGHT:
            x, y, r = np.array([-.15, .5, .05])
            self.patches.append(mpl.patches.Circle((x, y), radius=r, fc="k", ec="k", transform=self.transform, **self.kwargs))
    
    def get_patches(self):
        return self.patches
    
    def add_to_ax(self, ax):
        for patch in self.patches:
            ax.add_patch(patch)
    
    def move_to(self, square):
        self.affine_transform.translate(square.file - self.square.file, square.rank - self.square.rank)
        self.square = square
    
    def remove(self):
        for patch in self.patches:
            patch.remove()