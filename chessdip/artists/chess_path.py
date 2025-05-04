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
        
        self.slot = None
        
        self.real_pos = self.pos
        self.unit = None # unit vector following vector
        if self.direc == Direction.H:
            self.unit = np.array([1., 0.])
        elif self.direc == Direction.D:
            self.unit = np.array([np.sqrt(2) / 2., np.sqrt(2) / 2.])
        elif self.direc == Direction.V:
            self.unit = np.array([0., 1.])
        elif self.direc == Direction.A:
            self.unit = np.array([-np.sqrt(2) / 2., np.sqrt(2) / 2.])
        
        if not self.orient: # negative orientation
            self.unit = -self.unit
        
        self.shift_vec = np.asarray((self.unit[1], -self.unit[0])) # shifting to the right
    
    def __str__(self):
        return f"Vector at {self.pos} in direction {self.direc}"
    
    def __repr__(self):
        return f"Vector({self.pos}, {self.direc}, {self.orient}, bias={self.bias})"
    
    def set_bias(self, bias):
        self.bias = bias
    
    def set_shift(self, shift):
        self.real_pos = self.pos + shift * self.shift_vec
    
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
    
    def add_path(self, path_artist):
        # self.artists.append(path_artist)
        vectors = path_artist.compute_vectors(self.anchors)
        origin = np.asarray((path_artist.chess_path.start.file, path_artist.chess_path.start.rank))
        anchored_vectors = vectors[1:-1] if path_artist.junction is None else vectors[1:]
        for vector in anchored_vectors:
            # bias is sin(angle) between the Vector and the direction of the path start
            ref_vec = vector.unit if vector.orient else -vector.unit
            bias = np.cross(origin - vector.pos, ref_vec) / np.linalg.norm(origin - vector.pos)
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
    
    def shift_vectors(self):
        """
        in each rank/file/diagonal/antidiagonal with half-int coords, go
        through each anchor, compiling a list of all present vectors.
        
        This list is actually a list of lists, where each sublist is a set of
        vectors in the same slot.
        
        At each anchor, identify the vectors that are already on the list:
        for the remaining vectors, add them to the lists in between the
        already-present vectors; if no space then insert a new slot.
        
        Maybe insert the new slot in the middle, as best as possible? Don't do
        this on the first attempt.
        """
    
    def compute_vertices_from_vectors(self, path_artist):
        vectors = path_artist.vectors
        # print("hi", vectors)
        # Shift vectors except for the first and last one
        anchored_vectors = vectors[1:-1] if path_artist.junction is None else vectors[1:]
        for vector in anchored_vectors:
            for anchor in self.anchors:
                if np.all(anchor.pos == vector.pos) and anchor.direc == vector.direc:
                    shift = anchor.get_shift(vector)
                    vector.shift(shift, path_width=self.global_kwargs["path_width"]/30)
                    break
        # Find vertices
        vertices = []
        i = 0
        while i < len(vectors) - 1:
            vec0 = vectors[i]
            vec1 = vectors[i + 1]
            if vec0.direc == vec1.direc: # hopefully no switchbacks
                # need to insert a vector
                if vec0.get_shift() < vec1.get_shift():
                    new_direc = Direction((vec0.direc - 1) % 4)
                    new_orient = vec0.orient if vec0.direc > 0 else not vec0.orient
                else:
                    new_direc = Direction((vec0.direc + 1) % 4)
                    new_orient = vec0.orient if vec0.direc < 3 else not vec0.orient
                new_vec = ChessPathVector((vec0.pos + vec1.pos) / 2, new_direc, new_orient)
                vectors.insert(i + 1, new_vec)
                # need to compute bias as well
                for anchor in self.anchors:
                    if np.all(anchor.pos == new_vec.pos) and anchor.direc == new_vec.direc:
                        anchor.add_vector(new_vec)
                        shift = anchor.get_shift(new_vec)
                        # print(f"shifting {new_vec} by {shift}")
                        new_vec.shift(shift, path_width=self.global_kwargs["path_width"]/30)
                vec1 = new_vec
            # find intersection
            # print(vec0, vec1, vec0.real_pos, vec1.real_pos)
            x, _, _, _ = np.linalg.lstsq(np.array([vec0.unit, -vec1.unit]).T, vec1.real_pos - vec0.real_pos, rcond=None)
            v_inter = vec0.real_pos + x[0] * vec0.unit
            # print(f"{vec0} and {vec1} intersect at {v_inter}")
            vertices.append(v_inter)
            i += 1
        return vertices
    
    def get_intersection(self, path_artist, other_vertices, ignore_last=False, default=None):
        vec = path_artist.vectors[-2] if ignore_last else path_artist.vectors[-1]
        i = len(other_vertices) - 1
        while i > 0:
            v0 = other_vertices[i - 1]
            v1 = other_vertices[i]
            v_inter = _get_intersection(vec, v0, v1)
            if v_inter is not None:
                return [v_inter]
            i -= 1
        # Backup: add segment to connect to main vertex
        # define vector from default: direction/orient based on vec; get
        # intersection
        if default is not None:
            bias = np.cross(default - vec.real_pos, vec.unit) / np.linalg.norm(default - vec.real_pos)
            if bias > 0: # default destination is to the right of `vec`
                new_direc = Direction((vec.direc - 1) % 4)
                new_orient = vec.orient if vec.direc > 0 else not vec.orient
            else:
                new_direc = Direction((vec.direc - 1) % 4)
                new_orient = vec.orient if vec.direc < 3 else not vec.orient
            new_vec = ChessPathVector(default, new_direc, new_orient)
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

class ChessPathArtist:
    def __init__(self, chess_path, junction=None, shrinkA=0, shrinkB=0, clockwise=True):
        """
        `junction` is the location of the supported order's intersection with
        the landing square.
        clockwise: choose clockwise path over counter-clockwise when ambiguity
        """
        self.chess_path = chess_path
        self.junction = junction
        self.shrinkA = shrinkA
        self.shrinkB = shrinkB
        self.clockwise = clockwise
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
    
    def compute_vectors(self, anchors):
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        if not self.chess_path.valid:
            if self.junction is None:
                x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            else:
                x1, y1 = self.junction
            direc, orient = _get_direc_orient((x0, y0), (x1, y1))
            vec = ChessPathVector((x0, y0), direc, orient)
            
            first_direc = Direction((direc + 2) % 4)
            if direc == Direction.H or direc == Direction.D:
                first_orient = orient
            else:
                first_orient = not orient
            x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
            first_vec = ChessPathVector((x0, y0), first_direc, first_orient)
            first_vec.set_shift(self.shrinkA)
            
            last_direc = Direction((direc - 2) % 4)
            if direc == Direction.H or direc == Direction.D:
                last_orient = not orient
            else:
                last_orient = orient
            last_vec = ChessPathVector((x1, y1), last_direc, last_orient)
            last_vec.set_shift(self.shrinkB)
            self.vectors = [first_vec, vec, last_vec]
            return self.vectors
        
        first_vector = True
        for square in self.chess_path.intermediate_squares:
            x1, y1 = square.file, square.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                direc, orient = _get_direc_orient((x0, y0), (ax, ay))
                if first_vector:
                    self.vectors.append(ChessPathVector((ax, ay), direc, orient))
                    first_vector = False
                else:
                    self.vectors.append(ChessPathVector((x0, y0), direc, orient))
                connecting_vectors = self._connecting_vectors((ax, ay), (bx, by))
                self.vectors.extend(connecting_vectors)
                # x0, y0 = bx, by
                direc, orient = _get_direc_orient((bx, by), (x1, y1))
                self.vectors.append(ChessPathVector((bx, by), direc, orient))
            else:
                direc, orient = _get_direc_orient((x0, y0), (x1, y1))
                if first_vector:
                    first_vector = False
                else:
                    vectors.append(ChessPathVector((x0, y0), direc, orient))
                self.vectors.append(ChessPathVector(((x0 + x1) / 2, (y0 + y1) / 2), direc, orient))
            x0, y0 = x1, y1
        
        # Landing square
        if self.junction is None: # use shrinkB
            x1, y1 = self.chess_path.land.file, self.chess_path.land.rank
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
                # if the next square is not adjacent, then we add a connecting path
                ax, ay = self._closest_corner((x0, y0), (x1, y1), clockwise=self.clockwise)
                bx, by = self._closest_corner((x1, y1), (x0, y0), clockwise=not self.clockwise)
                direc, orient = _get_direc_orient((x0, y0), (ax, ay))
                if first_vector:
                    self.vectors.append(ChessPathVector((ax, ay), direc, orient))
                    first_vector = False
                else:
                    self.vectors.append(ChessPathVector((x0, y0), direc, orient))
                    # self.vectors.append(ChessPathVector((ax, ay), direc, orient))
                connecting_vectors = self._connecting_vectors((ax, ay), (bx, by))
                self.vectors.extend(connecting_vectors)
                x0, y0 = bx, by
                direc, orient = _get_direc_orient((bx, by), (x1, y1))
                self.vectors.append(ChessPathVector((bx, by), direc, orient))
            else:
                direc, orient = _get_direc_orient((x0, y0), (x1, y1))
                if first_vector:
                    first_vector = False
                else:
                    self.vectors.append(ChessPathVector((x0, y0), direc, orient))
                self.vectors.append(ChessPathVector(((x0 + x1) / 2, (y0 + y1) / 2), direc, orient))
            
            # add last vector: turn 90 degrees to the right
            last_direc = Direction((direc - 2) % 4)
            if direc == Direction.H or direc == Direction.D:
                last_orient = not orient
            else:
                last_orient = orient
            last_vec = ChessPathVector((x1, y1), last_direc, last_orient)
            last_vec.set_shift(self.shrinkB)
            self.vectors.append(last_vec)
        else:
            ax, ay = self._closest_corner((x0, y0), self.junction)
            direc, orient = _get_direc_orient((x0, y0), (ax, ay))
            if first_vector:
                self.vectors.append(ChessPathVector((ax, ay), direc, orient))
            else:
                self.vectors.append(ChessPathVector((x0, y0), direc, orient))
                self.vectors.append(ChessPathVector((ax, ay), direc, orient))
            
            connecting_vectors = self._connecting_vectors((ax, ay), self.junction)
            self.vectors.extend(connecting_vectors)
        
        # Add first vector so that the first turn is 90 degrees
        direc, orient = self.vectors[0].direc, self.vectors[0].orient
        first_direc = Direction((direc + 2) % 4)
        if direc == Direction.H or direc == Direction.D:
            first_orient = orient
        else:
            first_orient = not orient
        x0, y0 = self.chess_path.start.file, self.chess_path.start.rank
        first_vec = ChessPathVector((x0, y0), first_direc, first_orient)
        first_vec.set_shift(self.shrinkA)
        self.vectors = [first_vec] + self.vectors
        # print("chess path", self.chess_path, vectors)
        return self.vectors
    
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
        
        first_part = []
        second_part = []
        if in_horiz_edge:
            y_first = True
            for k in range(0, int(by - ay + y_sign * .5), y_sign):
                first_part.append(ChessPathVector((ax, ay + k), Direction.V, y_sign > 0))
                first_part.append(ChessPathVector((ax, ay + k + y_sign * .5), Direction.V, y_sign > 0))
            for k in range(0, int(bx - ax), x_sign):
                second_part.append(ChessPathVector((ax + k, by), Direction.H, x_sign > 0))
                second_part.append(ChessPathVector((ax + k + x_sign * .5, by), Direction.H, x_sign > 0))
            second_part.append(ChessPathVector((bx - x_sign * .5, by), Direction.H, x_sign > 0))
        elif in_vert_edge:
            y_first = False
            for k in range(0, int(bx - ax + x_sign * .5), x_sign):
                first_part.append(ChessPathVector((ax + k, ay), Direction.H, x_sign > 0))
                first_part.append(ChessPathVector((ax + k + x_sign * .5, ay), Direction.H, x_sign > 0))
            for k in range(0, int(by - ay), y_sign):
                second_part.append(ChessPathVector((bx, ay + k), Direction.V, y_sign > 0))
                second_part.append(ChessPathVector((bx, ay + k + y_sign * .5), Direction.V, y_sign > 0))
            second_part.append(ChessPathVector((bx, by - y_sign * .5), Direction.V, y_sign > 0))
        elif (self.clockwise and x_sign == y_sign) or (not self.clockwise and x_sign != y_sign):
            y_first = True
            y_first = True
            for k in range(0, int(by - ay + y_sign * .5), y_sign):
                first_part.append(ChessPathVector((ax, ay + k), Direction.V, y_sign > 0))
                first_part.append(ChessPathVector((ax, ay + k + y_sign * .5), Direction.V, y_sign > 0))
            for k in range(0, int(bx - ax + x_sign * .5), x_sign):
                second_part.append(ChessPathVector((ax + k, by), Direction.H, x_sign > 0))
                second_part.append(ChessPathVector((ax + k + x_sign * .5, by), Direction.H, x_sign > 0))
        else:
            y_first = False
            for k in range(0, int(bx - ax + x_sign * .5), x_sign):
                first_part.append(ChessPathVector((ax + k, ay), Direction.H, x_sign > 0))
                first_part.append(ChessPathVector((ax + k + x_sign * .5, ay), Direction.H, x_sign > 0))
            for k in range(0, int(by - ay + y_sign * .5), y_sign):
                second_part.append(ChessPathVector((bx, ay + k), Direction.V, y_sign > 0))
                second_part.append(ChessPathVector((bx, ay + k + y_sign * .5), Direction.V, y_sign > 0))
        
        if first_part and second_part:
            vectors = first_part
            ### Not working like I wanted...
            # if y_first:
            #     vectors.append(ChessPathVector((ax, by), Direction.D if x_sign == y_sign else Direction.A, x_sign > 0))
            # else:
            #     vectors.append(ChessPathVector((bx, ay), Direction.D if x_sign == y_sign else Direction.A, x_sign > 0))
            vectors.extend(second_part)
        else:
            vectors = first_part + second_part
        # print("connecting vectors", (ax, ay), (bx, by), in_horiz_edge, in_vert_edge, vectors)
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