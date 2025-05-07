# -*-coding:utf8-*-

import bisect
from collections import defaultdict
from enum import IntEnum
from matplotlib.path import Path
import numpy as np

from chessdip.board.chess_path import ChessPath

class Slope(IntEnum):
    H = 0 # horizontal
    D = 1 # diagonal
    V = 2 # vertical
    A = 3 # anti-diagonal

class ChessPathVector:
    """
    A path vector gives the direction that a path will take.
    """
    def __init__(self, pos, slope, orient, bias=0., check_more=0):
        self.pos = np.asarray(pos)
        self.slope = slope
        self.orient = orient
        self.bias = bias
        self.check_more = check_more
        
        self.slot = None
        
        self.real_pos = self.pos
        self.unit = None # unit vector following vector
        if self.slope == Slope.H:
            self.unit = np.array([1., 0.])
        elif self.slope == Slope.D:
            self.unit = np.array([np.sqrt(2) / 2., np.sqrt(2) / 2.])
        elif self.slope == Slope.V:
            self.unit = np.array([0., 1.])
        elif self.slope == Slope.A:
            self.unit = np.array([-np.sqrt(2) / 2., np.sqrt(2) / 2.])
        
        if not self.orient: # negative orientation
            self.unit = -self.unit
        
        self.shift_vec = np.asarray((self.unit[1], -self.unit[0])) # shifting to the right
    
    def __str__(self):
        return f"Vector at {self.pos} with slope {self.slope}"
    
    def __repr__(self):
        return f"Vector({self.pos}, {self.slope}, {self.orient}, bias={self.bias})"
    
    def set_bias(self, bias):
        self.bias = bias
    
    def add_bias(self, bias):
        self.bias += bias
    
    def set_check_more(self, check_more):
        self.check_more = check_more
    
    def set_shift(self, shift):
        self.real_pos = self.pos + shift * self.shift_vec
    
    def shift(self, n, path_width=.1):
        # shift vector by `n` increments. Should be parameterized by line width
        # or something.
        self.real_pos = self.pos + n * path_width * self.shift_vec * (1 if self.orient else -1)
    
    def get_shift(self):
        return np.dot(self.real_pos - self.pos, self.shift_vec)

# class VectorAnchor:
    """
    Manager for anchors at a given position and slope.
    
    Vectors are placed at anchors, which are at all half-integer coordinates.
    The anchor keeps track of the vectors that are located at its position,
    and computes (?) how these vectors are shifted to avoid overlapping paths.
    """
#     def __init__(self, pos, slope):
#         self.pos = pos
#         self.slope = slope
#         self.vectors = []
    
#     def add_vector(self, vector):
#         # do a sorted insert (w.r.t. bias) into the list
#         bisect.insort(self.vectors, vector, key=lambda v: v.bias)
#         pass
    
#     def get_shift(self, vector):
#         if vector not in self.vectors:
#             return None
#         idx = self.vectors.index(vector)
#         shift = idx - ((len(self.vectors) - 1) / 2)
#         return shift

class SortedVectorList(list):
    def __init__(self):
        super().__init__()
    
    def append(self, vector):
        bisect.insort(self, vector, key=lambda v: v.bias)

class VectorQuiver:
    def __init__(self):
        self.slots = []
    
    def __contains__(self, item):
        for slot in self.slots:
            if item in slot:
                return True
        return False
    
    def __str__(self):
        return self.slots.__str__()
    
    def clear(self):
        self.slots.clear()
    
    def disjoint(self, vectors):
        for vector in vectors:
            if vector in self:
                return False
        return True
    
    def index(self, vector):
        for i, slot in enumerate(self.slots):
            if vector in slot:
                return i
        return None
    
    def union(self, vectors):
        """
        Assume that `vectors` is sorted (by bias)
        """
        # Find slots containing elements of `vectors`
        indices = []
        prev_idx = 0
        current_idx = 0
        for i, vector in enumerate(vectors):
            j = self.index(vector)
            if j is not None:
                indices.append((i, j))
        indices.append((len(vectors), -1))
        
        j = 0 # slot index
        meta_idx = 0
        i0, j0 = indices[meta_idx] # current marked index
        for i, vector in enumerate(vectors):
            if i < i0 and j < j0:
                self.slots[j].append(vector)
                j += 1
            elif i < i0: # j == j0; need to create a new slot
                if j0 >= 0:
                    self.slots.insert(j0, [vector])
                else:
                    self.slots.append([vector])
            else: # i == i0; go to next already-present vector
                j = j0
                meta_idx += 1
                i0, j0 = indices[meta_idx]
                    

class ChessPathArtistManager:
    def __init__(self, visualizer, clockwise=True):
        self.clockwise = clockwise
        
        self.path_width = visualizer.global_kwargs["path_width"] / 30 # in data units
        self.anchors = defaultdict(SortedVectorList)
    
    def add_path(self, path_artist):
        vectors = path_artist.compute_vectors(self.anchors)
        origin = np.asarray((path_artist.chess_path.start.file, path_artist.chess_path.start.rank))
        anchored_vectors = vectors[1:-1] if path_artist.junction is None else vectors[1:]
        for vector in anchored_vectors:
            # bias is sin(angle) between the Vector and the direction of the path start
            ref_vec = vector.unit if vector.orient else -vector.unit
            if np.any(origin - vector.pos):
                bias = np.cross(origin - vector.pos, ref_vec) / np.linalg.norm(origin - vector.pos)
            else:
                bias = 0.
            vector.add_bias(bias)
    
    def shift_vectors(self):
        quiver = VectorQuiver()
        # horizontal
        for j in range(17):
            for i in range(17):
                self._aux_shift_vectors(quiver, i, j, Slope.H)
            self._shift_and_clear_quiver(quiver)
        
        # vertical
        for i in range(17):
            for j in range(17):
                self._aux_shift_vectors(quiver, i, j, Slope.V)
            self._shift_and_clear_quiver(quiver)
        
        # diagonal
        for k in range(33):
            for l in range(17 - abs(16 - k)):
                i = max(0, 16 - k) + l
                j = max(0, k - 16) + l
                self._aux_shift_vectors(quiver, i, j, Slope.D)
            self._shift_and_clear_quiver(quiver)
        
        # anti-diagonal
        for k in range(33):
            for l in range(17 - abs(16 - k)):
                i = max(0, k - 16) + l
                j = min(k, 16) - l
                self._aux_shift_vectors(quiver, i, j, Slope.A)
            self._shift_and_clear_quiver(quiver)
        
    def _aux_shift_vectors(self, quiver, i, j, slope):
        if (i, j, slope) in self.anchors:
            vectors = self.anchors[i, j, slope]
            if quiver.disjoint(vectors):
                self._shift_and_clear_quiver(quiver)
            quiver.union(vectors)
    
    def _shift_and_clear_quiver(self, quiver):
        n = len(quiver.slots)
        for i, slot in enumerate(quiver.slots):
            shift = i - ((n - 1) / 2)
            for vector in slot:
                vector.shift(shift, path_width=self.path_width)
        quiver.clear()
    
    def get_real_position_on_square(self, path_artist, square):
        i, j = pos_to_idx(square.file, square.rank)
        for slope in [Slope.H, Slope.D, Slope.V, Slope.A]:
            if (i, j, slope) in self.anchors:
                for vector in self.anchors[i, j, slope]:
                    if vector in path_artist.vectors:
                        square_pos = np.asarray((square.file, square.rank))
                        real_pos = vector.real_pos - vector.pos + square_pos
                        return real_pos
        return None
    
    def compute_vertices_from_vectors(self, path_artist):
        vectors = path_artist.get_all_vectors()
        # print("hi", vectors)
        vertices = []
        i = 0
        vec0 = vectors[0]
        while i < len(vectors) - 1:
            vec1 = vectors[i + 1]
            # find intersection
            x, _, _, _ = np.linalg.lstsq(np.array([vec0.unit, -vec1.unit]).T, vec1.real_pos - vec0.real_pos, rcond=None)
            min_x0 = x[0]
            min_idx = i + 1
            for k in range(vec0.check_more):
                next_vec = vectors[i + k + 2]
                x, _, _, _ = np.linalg.lstsq(np.array([vec0.unit, -next_vec.unit]).T, next_vec.real_pos - vec0.real_pos, rcond=None)
                if x[0] < min_x0:
                    min_x0 = x[0]
                    min_idx = i + k + 2
                    vec1 = next_vec
            v_inter = vec0.real_pos + min_x0 * vec0.unit
            # print(f"{vec0} and {vec1} intersect at {v_inter}")
            vertices.append(v_inter)
            vec0 = vec1
            i = min_idx
        return vertices
    
    def get_intersection(self, path_artist, other_vertices, default=None):
        vec = path_artist.vectors[-1]
        i = len(other_vertices) - 1
        while i > 0:
            v0 = other_vertices[i - 1]
            v1 = other_vertices[i]
            v_inter = _get_intersection(vec, v0, v1)
            if v_inter is not None:
                return [v_inter]
            i -= 1
        # Backup: add segment to connect to main vertex
        # define vector from default: slope/orient based on vec; get
        # intersection
        if default is not None:
            bias = np.cross(default - vec.real_pos, vec.unit) / np.linalg.norm(default - vec.real_pos)
            if bias > 0: # default destination is to the right of `vec`
                new_slope = Slope((vec.slope - 1) % 4)
                new_orient = vec.orient if vec.slope > 0 else not vec.orient
            else:
                new_slope = Slope((vec.slope + 1) % 4)
                new_orient = vec.orient if vec.slope < 3 else not vec.orient
            new_vec = ChessPathVector(default, new_slope, new_orient)
            x, _, _, _ = np.linalg.lstsq(np.array([vec.unit, -new_vec.unit]).T, new_vec.real_pos - vec.real_pos, rcond=None)
            v_inter = vec.real_pos + x[0] * vec.unit
            return [v_inter, default]
        elif path_artist.junction is not None:
            return [path_artist.junction]
        else:
            square = path_artist.chess_path.land
            return [(square.file, square.rank)]

def _get_intersection(vec, v0, v1):
    """
    Intersection of a Vector with the segment [v0, v1]
    """
    vec1 = np.array([v1[0] - v0[0], v1[1] - v0[1]])
    x, res, rank, sing = np.linalg.lstsq(
        np.array([vec.unit, -vec1]).T,
        np.asarray(v0) - np.asarray(vec.real_pos),
        rcond=None
    )
    if rank < 2:
        return None
    elif x[1] >= 0 and x[1] <= 1:
        v_inter = vec.real_pos + x[0] * vec.unit
        return v_inter
    else:
        return None

def pos_to_idx(x, y):
    return int(2 * x + 1), int(2 * y + 1)

def idx_to_pos(i, j):
    return (i - 1.) / 2., (j - 1.) / 2.

class ChessPathArtist:
    """
    Artist that compute the visual path of an order. The general design is
    that valid moves follow vertical, horizontal, and diagonal slopes,
    while invalid moves are a simple straight line from the starting square
    to the landing square.
    """
    def __init__(self, chess_path, junction=None, shrinkA=0, shrinkB=0, clockwise=True):
        """
        Parameters:
        ----------
        - chess_path: ChessPath. The path to be drawn.
        - junction: 2D point, optional. The junction is where a support path
            is aimed towards. This will usually be the intersection of the
            supported path and the landing square's boundary. Default value
            is None
        - shrinkA, shrinkB: float, optional. These parameters shorten the
            path at its start and end, respectively. Default value for both
            is 0.
        - clockwise: bool, optional. When True, the artist will choose the
            clockwise path over the counter-clockwise one when both paths
            are available. Default value is True.
        """
        self.chess_path = chess_path
        self.junction = junction
        self.shrinkA = shrinkA
        self.shrinkB = shrinkB
        self.clockwise = clockwise
        
        self.first_vec = None
        self.last_vec = None
        self.vectors = []
    
    def compute_path(self):
        if self.chess_path.valid:
            vertices = self.compute_vertices()
            codes = [Path.MOVETO] + (len(vertices) - 1) * [Path.LINETO]
            path = Path(vertices, codes)
        else:
            x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
            if self.junction is None:
                x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            else:
                x1, y1 = self.junction
            v0 = self._shrink_line((x1, y1), (x0, y0), self.shrinkA)
            v1 = self._shrink_line((x0, y0), (x1, y1), self.shrinkB)
            path = Path([v0, v1], [Path.MOVETO, Path.LINETO])
        return path
    
    def compute_vertices(self):
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
        if self.junction is None:
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                connecting_vertices = self._connecting_vertices((ax, ay), (bx, by))
                vertices.extend(connecting_vertices)
            last_vertex = self._shrink_line(vertices[-1], (x1, y1), self.shrinkB)
            vertices.append(last_vertex)
        else:
            ax, ay = self._closest_corner((x0, y0), self.junction)
            connecting_vertices = self._connecting_vertices((ax, ay), self.junction)
            vertices.extend(connecting_vertices)
        v0 = self._shrink_line(vertices[1], vertices[0], self.shrinkA)
        vertices[0] = v0
        return vertices
    
    def _closest_corner(self, square_center, target, clockwise=None):
        """
        Find closest corner of current square to the target point.
        Disambiguate using the object's clockwise flag.
        
        We assume that the target square lies outside of the current square,
        or on the boundary.
        
        Parameters:
        ----------
        - square_center: 2D point. Center of the current square.
        - target: 2D point. Target point.
        - clockwise: bool or None, optional. If True, then select the first
            corner that comes when proceeding clockwise. If False, then do
            the opposite. If None, then use the artist's `clockwise`
            parameter. Default value is None.
        """
        if clockwise is None:
            clockwise = self.clockwise
        x0, y0 = square_center
        target = np.asarray(target)
        corners = np.array([(x0 - .5, y0 - .5), (x0 - .5, y0 + .5), (x0 + .5, y0 + .5), (x0 + .5, y0 - .5)])
        # L1 and L2 distances are equivalent in this situtation, so we use L1.
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
        Find the vertices of a path that connect the start point to the end
        point, where the path can only go vertically and horizontally. We
        assume that the start is on a square corner
        (integer + .5 coordinates) and that the end is on a square edge
        (half-int coords).
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
        Shrink the point end towards start.
        """
        v_prev = np.asarray(start)
        v_next = np.asarray(end)
        direction = (v_next - v_prev)
        norm = np.linalg.norm(v_next - v_prev)
        if norm != 0:
            direction = direction / norm
        return tuple(v_next - shrink * direction)
    
    def get_vectors(self):
        return self.vectors
    
    def get_all_vectors(self):
        ret = []
        if self.first_vec is not None:
            ret.append(self.first_vec)
        ret.extend(self.vectors)
        if self.last_vec is not None:
            ret.append(self.last_vec)
        return ret
    
    def compute_vectors(self, anchors):
        """
        Assume the path is valid
        """
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        self.vectors = []
        current_direction = (None, None)
        current_vec = None
        squares = [(square.file, square.rank) for square in self.chess_path.intermediate_squares]
        if self.junction is None:
            squares.append((self.chess_path.land.file, self.chess_path.land.rank))
        
        for x1, y1 in squares:
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # non adjacent square
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                slope, orient = _get_slope_orient((x0, y0), (ax, ay))
                if current_vec is None:
                    self._get_first_vec((x0, y0), slope, orient)
                    current_vec = ChessPathVector((ax, ay), slope, orient)
                    current_direction = slope, orient
                    self.vectors.append(current_vec)
                elif (slope, orient) != current_direction:
                    current_vec = ChessPathVector((x0, y0), slope, orient)
                    self.vectors.append(current_vec)
                    anchors[*pos_to_idx(x0, y0), slope].append(current_vec)
                else:
                    anchors[*pos_to_idx(x0, y0), slope].append(current_vec)
                anchors[*pos_to_idx(ax, ay), slope].append(current_vec)
                connecting_vectors = self._connecting_vectors((ax, ay), (bx, by), anchors)
                self.vectors.extend(connecting_vectors)
                
                slope, orient = _get_slope_orient((bx, by), (x1, y1))
                current_vec = ChessPathVector((bx, by), slope, orient)
                current_direction = slope, orient
                self.vectors.append(current_vec)
                anchors[*pos_to_idx(bx, by), slope].append(current_vec)
            else:
                slope, orient = _get_slope_orient((x0, y0), (x1, y1))
                ax, ay = (x0 + x1) / 2, (y0 + y1) / 2
                if current_vec is None:
                    self._get_first_vec((x0, y0), slope, orient)
                    current_vec = ChessPathVector((ax, ay), slope, orient)
                    current_direction = slope, orient
                    self.vectors.append(current_vec)
                elif (slope, orient) != current_direction: # should not happen
                    current_vec = ChessPathVector((x0, y0), slope, orient)
                    current_direction = slope, orient
                    self.vectors.append(current_vec)
                    anchors[*pos_to_idx(x0, y0), slope].append(current_vec)
                else:
                    anchors[*pos_to_idx(x0, y0), slope].append(current_vec)
                anchors[*pos_to_idx(ax, ay), slope].append(current_vec)
            x0, y0 = x1, y1
        
        # Landing square
        if self.junction is None:
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            self._get_last_vec((x1, y1), *current_direction)
        else:
            ax, ay = self._closest_corner((x0, y0), self.junction)
            slope, orient = _get_slope_orient((x0, y0), (ax, ay))
            if current_vec is None:
                self._get_first_vec((x0, y0), slope, orient)
                current_vec = ChessPathVector((ax, ay), slope, orient)
                self.vectors.append(current_vec)
            elif (slope, orient) != current_direction:
                current_vec = ChessPathVector((x0, y0), slope, orient)
                self.vectors.append(current_vec)
                anchors[*pos_to_idx(x0, y0), slope].append(current_vec)
            else:
                anchors[*pos_to_idx(x0, y0), slope].append(current_vec)
            anchors[*pos_to_idx(ax, ay), slope].append(current_vec)
            connecting_vectors = self._connecting_vectors((ax, ay), self.junction, anchors)
            self.vectors.extend(connecting_vectors)
        # print("chess path", self.chess_path, self.vectors)
        return self.vectors
    
    def _connecting_vectors(self, start, end, anchors):
        """
        Experimental; like `_connecting_vertices` but with Vectors.
        """
        ax, ay = start
        bx, by = end
        x_sign = 1 if bx - ax >= 0 else -1
        y_sign = 1 if by - ay >= 0 else -1
        in_horiz_edge = not (bx + .5).is_integer()
        in_vert_edge = not (by + .5).is_integer()
        
        first_part = []
        second_part = []
        if in_horiz_edge:
            y_first = True
        elif in_vert_edge:
            y_first = False
        elif (self.clockwise and x_sign == y_sign) or (not self.clockwise and x_sign != y_sign):
            y_first = True
        else:
            y_first = False
        
        ret = []
        if y_first:
            if ay != by:
                current_vec = ChessPathVector((ax, ay), Slope.V, y_sign > 0)
                ret.append(current_vec)
                for y in np.arange(ay, by, y_sign * .5):
                    anchors[*pos_to_idx(ax, y), Slope.V].append(current_vec)
            if ax != bx:
                current_vec = ChessPathVector((ax, by), Slope.H, x_sign > 0)
                ret.append(current_vec)
                for x in np.arange(ax, bx, x_sign * .5):
                    anchors[*pos_to_idx(x, by), Slope.H].append(current_vec)
        else:
            if ax != bx:
                current_vec = ChessPathVector((ax, ay), Slope.H, x_sign > 0)
                ret.append(current_vec)
                for x in np.arange(ax, bx, x_sign * .5):
                    anchors[*pos_to_idx(x, ay), Slope.H].append(current_vec)
            if ay != by:
                current_vec = ChessPathVector((bx, ay), Slope.V, y_sign > 0)
                ret.append(current_vec)
                for y in np.arange(ay, by, y_sign * .5):
                    anchors[*pos_to_idx(bx, y), Slope.V].append(current_vec)
                        
        if len(ret) >= 2:
            corner = (ax, by) if y_first else (bx, ay)
            corner_slope = Slope.D if x_sign == y_sign else Slope.A
            corner_vec = ChessPathVector(corner, corner_slope, x_sign > 0, bias=x_sign * (2 if y_first else -2))
            anchors[*pos_to_idx(*corner), corner_slope].append(corner_vec)
            ret.insert(1, corner_vec)
            ret[0].set_check_more(1)
        # print("connecting vectors", (ax, ay), (bx, by), in_horiz_edge, in_vert_edge, ret)
        return ret
    
    def _get_first_vec(self, pos, slope, orient):
        first_slope = Slope((slope + 2) % 4)
        if slope == Slope.H or slope == Slope.D:
            first_orient = orient
        else:
            first_orient = not orient
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        self.first_vec = ChessPathVector(pos, first_slope, first_orient)
        self.first_vec.set_shift(self.shrinkA)
    
    def _get_last_vec(self, pos, slope, orient):
        last_slope = Slope((slope - 2) % 4)
        if slope == Slope.H or slope == Slope.D:
            last_orient = not orient
        else:
            last_orient = orient
        self.last_vec = ChessPathVector(pos, last_slope, last_orient)
        self.last_vec.set_shift(self.shrinkB)

def _get_slope_orient(v0, v1):
    x0, y0 = v0
    x1, y1 = v1
    if y0 == y1:
        return Slope.H, x1 > x0
    elif x0 == x1:
        return Slope.V, y1 > y0
    elif x1 - x0 == y1 - y0:
        return Slope.D, y1 > y0
    elif x1 - x0 == y0 - y1:
        return Slope.A, y1 > y0