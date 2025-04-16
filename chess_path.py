# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np

from power import Power
from square import Square
from piece import *

class ChessPath:
    def __init__(self, piece, landing_square):
        self.piece = piece
        self.start = self.piece.square
        self.land = landing_square
        
        self.intermediate_squares = []
        self.valid = self._validate_path()
        
        self.artist = ChessPathArtist(self)
    
    def _validate_path(self):
        dfile = self.land.file - self.start.file
        drank = self.land.rank - self.start.rank
        dfile_sign = 1 if dfile >= 0 else -1
        drank_sign = 1 if drank >= 0 else -1
        match self.piece.code:
            case Piece.KING:
                if abs(dfile) <= 1 and abs(drank) <= 1:
                    return True
            case Piece.ROOK:
                if dfile == 0:
                    ranks = range(self.start.rank, self.land.rank, drank_sign)[1:]
                    self.intermediate_squares = [Square(rank=y, file=self.start.file) for y in ranks]
                    return True
                elif drank == 0:
                    files = range(self.start.file, self.land.file, dfile_sign)[1:]
                    self.intermediate_squares = [Square(rank=self.start.rank, file=x) for x in files]
                    return True
            case Piece.BISHOP:
                if abs(dfile) == abs(drank):
                    self.intermediate_squares = [
                        Square(file=x, rank=y) for x, y in zip(
                            range(self.start.file + 1, self.land.file, dfile_sign),
                            range(self.start.rank + 1, self.land.rank, drank_sign)
                        )
                    ]
                    return True
            case Piece.KNIGHT:
                if (abs(drank) == 2 and abs(dfile) == 1) or (abs(dfile) == 2 and abs(drank) == 1):
                    return True
            case Piece.PAWN:
                if drank == 1 and abs(dfile) <= 1:
                    return True
                
                if self.piece.power.side == Power.WHITE:
                    home_rank_pawn = self.land.rank < 2
                elif self.piece.power.side == Power.BLACK:
                    home_rank_pawn = self.land.rank >= 6
                if home_rank_pawn and drank == 2 and dfile == 0:
                    self.intermediate_squares.append(Square(rank=self.start.rank + 1, file=self.start.file))
                    return True
            case _:
                return False
        return False
    

class ChessPathArtist:
    def __init__(self, chess_path, support=None, clockwise=True):
        """
        clockwise: choose clockwise path over counter-clockwise when ambiguity
        """
        self.chess_path = chess_path
        self.clockwise = clockwise
        
        # self.squares = [chess_path.starting_square] + chess_path.intermediate_squares + [chess_path.landing_square]
        if self.chess_path.valid:
            vertices = self.compute_vertices(support=support)
            codes = [Path.MOVETO] + (len(vertices) - 1) * [Path.LINETO]
            self.path = Path(vertices, codes)
        else:
            x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            self.path = Path([(x0, y0), (x1, y1)], [Path.MOVETO, Path.LINETO])
    
    def compute_vertices(self, support=None):
        """
        `support` is the location of the supported order's intersection with
        the landing square.
        """
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        vertices = [(x0, y0)]
        for square in self.chess_path.intermediate_squares:
            x1, y1 = square.file, square.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1))
                bx, by = self._closest_corner((x1, y1), (x0, y0))
                connecting_vertices = self._connecting_vertices((ax, ay), (bx, by))
                vertices.extend(connecting_vertices)
            vertices.append((x1, y1))
            x0, y0 = x1, y1
        
        # Landing square
        if support is None:
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1))
                bx, by = self._closest_corner((x1, y1), (x0, y0))
                connecting_vertices = self._connecting_vertices((ax, ay), (bx, by))
                vertices.extend(connecting_vertices)
            vertices.append((x1, y1))
        else:
            ax, ay = self._closest_corner((x0, y0), support)
            connecting_vertices = self._connecting_vertices((ax, ay), support)
            vertices.extend(connecting_vertices)
        return vertices
    
    def _closest_corner(self, square_center, target):
        """
        Find closest corner of current square to the target point.
        Disambiguate using the object's clockwise flag.
        
        We assume that the target square lies outside of the current square.
        
        L1 and L2 distances are equivalent in this situtation.
        """
        x0, y0 = square_center
        target = np.asarray(target)
        corners = np.array([(x0 - .5, y0 - .5), (x0 - .5, y0 + .5), (x0 + .5, y0 + .5), (x0 + .5, y0 - .5)])
        dists = np.sum(np.abs(np.subtract(target, corners)), axis=1)
        candidate_idx = (dists == dists.min()).nonzero()[0]
        if len(candidate_idx) > 1 and candidate_idx[1] != candidate_idx[0] + 1:
            return corners[candidate_idx[1]]
        else:
            return corners[candidate_idx[0]]
    
    def _connecting_vertices(self, start, end):
        """
        Assuming start is on a square corner (integer + .5 coordinates)
        and end is on a square edge
        """
        ax, ay = start
        bx, by = end
        x_sign = 1 if bx - ax >= 0 else -1
        y_sign = 1 if by - ay >= 0 else -1
        in_horiz_edge = not (bx + .5).is_integer()
        in_vert_edge = not (by + .5).is_integer()
        
        vertices = []
        if in_horiz_edge:
            # do y first
            vertices.extend([(ax, ay + k) for k in range(0, int(by - ay), y_sign)])
            vertices.extend([(ax + k, by) for k in range(0, int(bx - ax), x_sign)])
        elif in_vert_edge:
            # do x first
            vertices.extend([(ax + k, ay) for k in range(0, int(bx - ax), x_sign)])
            vertices.extend([(bx, ay + k) for k in range(0, int(by - ay), y_sign)])
        elif (self.clockwise and x_sign == y_sign) or (not self.clockwise and x_sign != y_sign):
            # do y first
            vertices.extend([(ax, ay + k) for k in range(0, int(by - ay), y_sign)])
            vertices.extend([(ax + k, by) for k in range(0, int(bx - ax), x_sign)])
        else:
            # do x first
            vertices.extend([(ax + k, ay) for k in range(0, int(bx - ax), x_sign)])
            vertices.extend([(bx, ay + k) for k in range(0, int(by - ay), y_sign)])
        vertices.append((bx, by))
        return vertices
            
        