# -*-coding:utf8-*-

import bisect
from enum import IntEnum
from matplotlib.path import Path
import numpy as np

from chessdip.board.chess_path import ChessPath

class Direction(IntEnum):
    H = 0 # horizontal
    D = 1 # diagonal
    V = 2 # vertical
    A = 3 # anti-diagonal

class ChessPathVector:
    """
    A path vector gives the direction that a path will take.
    """
    def __init__(self, pos, direc, orient, bias=0.):
        self.pos = np.asarray(pos)
        self.direc = direc
        self.orient = orient
        self.bias = bias
        
        self.real_pos = pos
        self.unit = None # unit vector following vector
        if self.direc == Direction.H:
            self.unit = np.array([1., 0.])
        elif self.direc == Direction.D:
            self.unit = np.array([np.sqrt(2), np.sqrt(2)])
        elif self.direc == Direction.V:
            self.unit = np.array([0., 1.])
        elif self.direc == Direction.A:
            self.unit = np.array([-np.sqrt(2), np.sqrt(2)])
        
        if not self.orient: # negative orientation
            self.unit = -self.unit
        
        self.shift_vec = np.asarray((self.unit[1], -self.unit[0])) # shifting to the right
    
    def __str__(self):
        return f"Vector at {self.pos} in direction {self.direc}"
    
    def __repr__(self):
        return f"Vector({self.pos}, {self.direc}, bias={self.bias})"
    
    def set_bias(self, bias):
        self.bias = bias
    
    def shift(self, n, path_width=.1):
        # shift vector by `n` increments. Should be parameterized by line width
        # or something.
        self.real_pos = self.pos + n * path_width * self.shift_vec * (1 if self.orient else -1)
    
    def get_shift(self):
        return np.dot(self.real_pos - self.pos, self.shift_vec)
    
    def get_orient(self):
        return self.orient

class VectorAnchor:
    """
    Manager for anchors at a given position and slope (direction or its
    opposite).
    
    Vectors are placed at anchors, which are at all half-integer coordinates.
    The anchor keeps track of the vectors that are located at its position,
    and computes (?) how these vectors are shifted to avoid overlapping paths.
    """
    def __init__(self, pos, direc):
        self.pos = pos
        self.direc = direc
        self.vectors = []
    
    def add_vector(self, vector):
        # do a sorted insert (w.r.t. bias) into the list
        bisect.insort(self.vectors, vector, key=lambda v: v.bias)
        pass
    
    def get_shift(self, vector):
        if vector not in self.vectors:
            return None
        idx = self.vectors.index(vector)
        shift = idx - ((len(self.vectors) - 1) / 2)
        return shift

class ChessPathArtistManager:
    def __init__(self, visualizer, clockwise=True):
        self.global_kwargs = visualizer.global_kwargs
        self.clockwise = clockwise
        
        # self.artists = []
        self.anchors = [] # dict of {(half-int, half-int): VectorAnchor}
    
    def add_path(self, path_artist, last_vec=None, shrinkA=0, shrinkB=0):
        # path_artist = ChessPathArtist(ChessPath(path))
        # self.artists.append(path_artist)
        vectors = path_artist.compute_vectors(last_vec=last_vec, shrinkA=shrinkA, shrinkB=shrinkB)
        origin = np.asarray((path_artist.chess_path.start.file, path_artist.chess_path.start.rank))
        for vector in vectors:
            # bias is angle between the Vector and the direction of the path start
            bias = np.arctan2(np.cross(vector.unit, origin - vector.pos), np.dot(vector.unit, origin - vector.pos))
            vector.set_bias(bias)
            found_anchor = False
            for anchor in self.anchors:
                if np.all(anchor.pos == vector.pos) and anchor.direc == vector.direc:
                    anchor.add_vector(vector)
                    found_anchor = True
                    break
            if not found_anchor:
                anchor = VectorAnchor(vector.pos, vector.direc)
                anchor.add_vector(vector)
                self.anchors.append(anchor)
    
    def get_path_from_vectors(self, path_artist):
        # compute path for artist
        # for each pair of consecutive vectors, compute intersection: these
        # are the vertices of the path
        """
        Special handling when two consecutive vectors are the same direction:
        add Vector in between with the appropriate direction
        """
        vectors = path_artist.vectors
        # print("hi", vectors)
        # Shift vectors except for the first and last one
        for vector in vectors[1:-1]:
            for anchor in self.anchors:
                if np.all(anchor.pos == vector.pos) and anchor.direc == vector.direc:
                    shift = anchor.get_shift(vector)
                    # print(f"shifting {vector} by {shift}")
                    vector.shift(shift, path_width=self.global_kwargs["path_width"]/30)
                    break
        # Find vertices
        vertices = []
        i = 0
        while i < len(vectors) - 1:
            v0 = vectors[i]
            v1 = vectors[i + 1]
            if v0.direc == v1.direc: # hopefully no switchbacks
                # need to insert a vector
                
                # print("ok", v0.bias, v1.bias)
                if v0.get_shift() < v1.get_shift():
                    new_direc = Direction((v0.direc - 1) % 4)
                    # print("hi", v0.direc, new_direc)
                    new_orient = v0.orient if v0.direc > 0 else not v0.orient
                else:
                    new_direc = Direction((v0.direc + 1) % 4)
                    # print("hej", v0.direc, new_direc)
                    new_orient = v0.orient if v0.direc < 3 else not v0.orient
                new_vec = ChessPathVector((v0.pos + v1.pos) / 2, new_direc, new_orient)
                vectors.insert(i + 1, new_vec)
                # need to compute bias as well
                for anchor in self.anchors:
                    if np.all(anchor.pos == new_vec.pos) and anchor.direc == new_vec.direc:
                        anchor.add_vector(new_vec)
                        shift = anchor.get_shift(new_vec)
                        # print(f"shifting {new_vec} by {shift}")
                        new_vec.shift(shift, path_width=self.global_kwargs["path_width"]/30)
                v1 = new_vec
            # find intersection
            x, _, _, _ = np.linalg.lstsq(np.array([v0.unit, -v1.unit]).T, v1.real_pos - v0.real_pos, rcond=None)
            v_inter = v0.real_pos + x[0] * v0.unit
            # print(f"{v0} and {v1} intersect at {v_inter}")
            vertices.append(v_inter)
            i += 1
        # Build path
        codes = [Path.MOVETO] + (len(vertices) - 1) * [Path.LINETO]
        path = Path(vertices, codes)
        return path
        

class ChessPathArtist:
    def __init__(self, chess_path, clockwise=True):
        """
        clockwise: choose clockwise path over counter-clockwise when ambiguity
        """
        self.chess_path = chess_path
        self.clockwise = clockwise
    
    def compute_vectors(self, last_vec=None, shrinkA=0, shrinkB=0):
        """
        `junction` is the location of the supported order's intersection with
        the landing square.
        """
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        vectors = []
        for square in self.chess_path.intermediate_squares:
            x1, y1 = square.file, square.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                direc, orient = _get_direc_orient((x0, y0), (ax, ay))
                vectors.append(ChessPathVector((x0, y0), direc, orient))
                connecting_vectors = self._connecting_vectors((ax, ay), (bx, by))
                vectors.extend(connecting_vectors)
                x0, y0 = bx, by
            direc, orient = _get_direc_orient((x0, y0), (x1, y1))
            vectors.append(ChessPathVector((x0, y0), direc, orient))
            x0, y0 = x1, y1
        
        # Landing square
        if last_vec is None:
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                direc, orient = _get_direc_orient((x0, y0), (ax, ay))
                vectors.append(ChessPathVector((x0, y0), direc, orient))
                connecting_vectors = self._connecting_vectors((ax, ay), (bx, by))
                vectors.extend(connecting_vectors)
                x0, y0 = bx, by
            direc, orient = _get_direc_orient((x0, y0), (x1, y1))
            vectors.append(ChessPathVector((x0, y0), direc, orient))
            vectors.append(ChessPathVector((x1, y1), direc, orient)) # to make space for arrow
            
            # add last vector: turn 90 degrees to the right
            last_direc = Direction((direc - 2) % 4)
            if direc == Direction.H or Direction.D:
                last_orient = not orient
            else:
                last_orient = orient
            vectors.append(ChessPathVector((x1, y1), last_direc, last_orient, bias=shrinkB))
        else:
            ax, ay = self._closest_corner((x0, y0), last_vec.pos)
            direc, orient = _get_direc_orient((x0, y0), (ax, ay))
            vectors.append(ChessPathVector((x0, y0), direc, orient))
            
            connecting_vectors = self._connecting_vectors((ax, ay), last_vec.pos)
            vectors.extend(connecting_vectors)
            vectors.append(last_vec)
        
        # Add first vector so that the first turn is 90 degrees
        direc, orient = vectors[0].direc, vectors[0].orient
        first_direc = Direction((direc + 2) % 4)
        if direc == Direction.H or Direction.D:
            first_orient = not orient
        else:
            first_orient = orient
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        vectors = [ChessPathVector((x0, y0), first_direc, first_orient, bias=shrinkA)] + vectors
        
        self.vectors = vectors
        return vectors
    
    def compute_path(self, junction=None, shrinkA=0, shrinkB=0):
        if self.chess_path.valid:
            vertices = self.compute_vertices(junction=junction, shrinkA=shrinkA, shrinkB=shrinkB)
            codes = [Path.MOVETO] + (len(vertices) - 1) * [Path.LINETO]
            path = Path(vertices, codes)
        else:
            x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
            if junction is None:
                x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            else:
                x1, y1 = junction
            v0 = self._shrink_line((x1, y1), (x0, y0), shrinkA)
            v1 = self._shrink_line((x0, y0), (x1, y1), shrinkB)
            path = Path([v0, v1], [Path.MOVETO, Path.LINETO])
        return path
    
    def compute_vertices(self, junction=None, shrinkA=0, shrinkB=0):
        """
        `junction` is the location of the supported order's intersection with
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
        if junction is None:
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                connecting_vertices = self._connecting_vertices((ax, ay), (bx, by))
                vertices.extend(connecting_vertices)
            last_vertex = self._shrink_line(vertices[-1], (x1, y1), shrinkB)
            vertices.append(last_vertex)
        else:
            ax, ay = self._closest_corner((x0, y0), junction)
            connecting_vertices = self._connecting_vertices((ax, ay), junction)
            vertices.extend(connecting_vertices)
        v0 = self._shrink_line(vertices[1], vertices[0], shrinkA)
        vertices[0] = v0
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
        if len(candidate_idx) == 1:
            return corners[candidate_idx[0]]
        else:
            if candidate_idx[1] != candidate_idx[0] + 1:
                return corners[candidate_idx[1 if clockwise else 0]]
            else:
                return corners[candidate_idx[0 if clockwise else 1]]
    
    def _connecting_vertices(self, start, end):
        """
        Assuming start is on a square corner (integer + .5 coordinates)
        and end is on a square edge (half-int coords)
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
        """
        Shrink the point end towards start
        """
        v_prev = np.asarray(start)
        v_next = np.asarray(end)
        direction = (v_next - v_prev)
        norm = np.linalg.norm(v_next - v_prev)
        if norm != 0:
            direction = direction / norm
        return tuple(v_next - shrink * direction)
    
    def _connecting_vectors(self, start, end):
        """
        Assuming start is on a square corner (integer + .5 coordinates)
        and end is on a square edge (half-int coords)
        """
        ax, ay = start
        bx, by = end
        x_sign = 1 if bx - ax >= 0 else -1
        y_sign = 1 if by - ay >= 0 else -1
        in_horiz_edge = not (bx + .5).is_integer()
        in_vert_edge = not (by + .5).is_integer()
        
        vectors = []
        if in_horiz_edge:
            y_first = True
        elif in_vert_edge:
            y_first = False
        elif (self.clockwise and x_sign == y_sign) or (not self.clockwise and x_sign != y_sign):
            y_first = True
        else:
            y_first = False
        
        if y_first:
            vectors.extend([ChessPathVector((ax, ay + k + y_sign * .5), Direction.V, y_sign > 0) for k in range(0, int(by - ay), y_sign)])
            vectors.append(ChessPathVector((ax, by), Direction.D if x_sign == y_sign else Direction.A, x_sign > 0))
            vectors.extend([ChessPathVector((ax + k + x_sign * .5, by), Direction.H, x_sign > 0) for k in range(0, int(bx - ax), x_sign)])
        else:
            vectors.extend([ChessPathVector((ax + k + x_sign * .5, ay), Direction.H, x_sign > 0) for k in range(0, int(bx - ax), x_sign)])
            vectors.append(ChessPathVector((ax, by), Direction.D if x_sign == y_sign else Direction.A, x_sign > 0))
            vectors.extend([ChessPathVector((bx, ay + k + y_sign * .5), Direction.V, y_sign > 0) for k in range(0, int(by - ay), y_sign)])
        return vectors

def _get_direc_orient(v0, v1):
    x0, y0 = v0
    x1, y1 = v1
    if y0 == y1:
        return Direction.H, x1 > x0
    elif x0 == x1:
        return Direction.V, y1 > y0
    elif x1 - x0 == y1 - y0:
        return Direction.D, y1 > y0
    elif x1 - x0 == y0 - y1:
        return Direction.A, y1 > y0