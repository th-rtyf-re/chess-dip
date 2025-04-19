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
        
        self.valid, self.intermediate_squares = ChessPath.validate_path(self.piece, self.start, self.land)
        
        self.artist = ChessPathArtist(self)
    
    def validate_path(piece, start, land):
        valid = False
        intermediate_squares = []
        dfile = land.file - start.file
        drank = land.rank - start.rank
        dfile_sign = 1 if dfile >= 0 else -1
        drank_sign = 1 if drank >= 0 else -1
        file_range = range(start.file, land.file, dfile_sign)[1:]
        rank_range = range(start.rank, land.rank, drank_sign)[1:]
        match piece.code:
            case Piece.KING:
                if abs(dfile) <= 1 and abs(drank) <= 1:
                    valid = True
            case Piece.ROOK:
                if dfile == 0:
                    intermediate_squares = [Square(rank=y, file=start.file) for y in rank_range]
                    valid = True
                elif drank == 0:
                    intermediate_squares = [Square(rank=start.rank, file=x) for x in file_range]
                    valid = True
            case Piece.BISHOP:
                if abs(dfile) == abs(drank):
                    intermediate_squares = [Square(file=x, rank=y) for x, y in zip(file_range, rank_range)]
                    valid = True
            case Piece.KNIGHT:
                if (abs(drank) == 2 and abs(dfile) == 1) or (abs(dfile) == 2 and abs(drank) == 1):
                    valid = True
            case Piece.PAWN:
                
                
                home_rank_pawn = True
                if piece.power.side == Power.WHITE:
                    if drank == 1 and abs(dfile) <= 1:
                        valid = True
                    elif start.rank < 2 and drank == 2 and dfile == 0:
                        intermediate_squares.append(Square(rank=start.rank + 1, file=start.file))
                        valid = True
                elif piece.power.side == Power.BLACK:
                    print(drank, dfile, start.rank)
                    if drank == -1 and abs(dfile) <= 1:
                        valid = True
                    elif start.rank >= 6 and drank == -2 and dfile == 0:
                        intermediate_squares.append(Square(rank=start.rank - 1, file=start.file))
                        valid = True
            case _:
                pass
        return valid, intermediate_squares
    

class ChessPathArtist:
    def __init__(self, chess_path, clockwise=True):
        """
        clockwise: choose clockwise path over counter-clockwise when ambiguity
        """
        self.chess_path = chess_path
        self.clockwise = clockwise
        
        # self.squares = [chess_path.starting_square] + chess_path.intermediate_squares + [chess_path.landing_square]
    
    def compute_path(self, support=None, shrink=0):
        if self.chess_path.valid:
            vertices = self.compute_vertices(support=support, shrink=shrink)
            codes = [Path.MOVETO] + (len(vertices) - 1) * [Path.LINETO]
            path = Path(vertices, codes)
        else:
            x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            last_vertex = self._shrink_line((x0, y0), (x1, y1), shrink)
            path = Path([(x0, y0), last_vertex], [Path.MOVETO, Path.LINETO])
        return path
    
    def compute_vertices(self, support=None, shrink=0):
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
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                connecting_vertices = self._connecting_vertices((ax, ay), (bx, by))
                vertices.extend(connecting_vertices)
            vertices.append((x1, y1))
            x0, y0 = x1, y1
        
        # Landing square
        if support is None:
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                connecting_vertices = self._connecting_vertices((ax, ay), (bx, by))
                vertices.extend(connecting_vertices)
            last_vertex = self._shrink_line(vertices[-1], (x1, y1), shrink)
            vertices.append(last_vertex)
        else:
            ax, ay = self._closest_corner((x0, y0), support)
            connecting_vertices = self._connecting_vertices((ax, ay), support)
            vertices.extend(connecting_vertices)
        return vertices
    
    def _closest_corner(self, square_center, target, clockwise=None):
        """
        Find closest corner of current square to the target point.
        Disambiguate using the object's clockwise flag.
        
        We assume that the target square lies outside of the current square.
        
        L1 and L2 distances are equivalent in this situtation.
        """
        if clockwise is None:
            clockwise = self.clockwise
        x0, y0 = square_center
        target = np.asarray(target)
        corners = np.array([(x0 - .5, y0 - .5), (x0 - .5, y0 + .5), (x0 + .5, y0 + .5), (x0 + .5, y0 - .5)])
        dists = np.sum(np.abs(np.subtract(target, corners)), axis=1)
        candidate_idx = (dists == dists.min()).nonzero()[0]
        if len(candidate_idx) > 1 and candidate_idx[1] != candidate_idx[0] + 1:
            if clockwise:
                return corners[candidate_idx[1]]
            else:
                return corners[candidate_idx[0]]
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
            vertices.extend([(ax, ay + k) for k in range(0, int(by - ay + y_sign), y_sign)])
            vertices.extend([(ax + k, by) for k in range(0, int(bx - ax + x_sign), x_sign)])
        elif in_vert_edge:
            # do x first
            vertices.extend([(ax + k, ay) for k in range(0, int(bx - ax + x_sign), x_sign)])
            vertices.extend([(bx, ay + k) for k in range(0, int(by - ay + y_sign), y_sign)])
        elif (self.clockwise and x_sign == y_sign) or (not self.clockwise and x_sign != y_sign):
            # do y first
            vertices.extend([(ax, ay + k) for k in range(0, int(by - ay + y_sign), y_sign)])
            vertices.extend([(ax + k, by) for k in range(0, int(bx - ax + x_sign), x_sign)])
        else:
            # do x first
            vertices.extend([(ax + k, ay) for k in range(0, int(bx - ax + x_sign), x_sign)])
            vertices.extend([(bx, ay + k) for k in range(0, int(by - ay + y_sign), y_sign)])
        vertices.append((bx, by))
        return vertices
    
    def _shrink_line(self, start, end, shrink):
        v_prev = np.asarray(start)
        v_next = np.asarray(end)
        direction = (v_next - v_prev)
        norm = np.linalg.norm(v_next - v_prev)
        if norm != 0:
            direction = direction / norm
        return tuple(v_next - shrink * direction)
        