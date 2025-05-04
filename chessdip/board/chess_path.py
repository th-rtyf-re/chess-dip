# -*-coding:utf8-*-

from chessdip.board.power import Side
from chessdip.board.square import Square
from chessdip.board.piece import Piece

class ChessPath:
    def __init__(self, piece, landing_square, exception=None):
        """
        For exceptions, we assume that the path is already validated.
        """
        self.piece = piece
        self.start = self.piece.square
        self.land = landing_square
        
        if exception is None:
            self.valid, self.intermediate_squares = ChessPath.validate_path(self.piece, self.start, self.land)
        elif exception == "castle":
            self.valid = True
            if self.piece.code == Piece.KING:
                self.intermediate_squares = []
            elif self.piece.code == Piece.ROOK:
                _, squares = ChessPath.validate_path(self.piece, self.start, self.land)
                self.intermediate_squares = squares[:-1]
        elif exception == "en_passant":
            dfile = self.land.file - self.start.file
            drank = self.land.rank - self.start.rank
            if piece.power.side == Side.WHITE:
                self.valid = abs(dfile) == 1 and abs(drank) in (0, 2)
            else:
                self.valid = abs(dfile) == 1 and abs(drank) in (0, -2)
            self.intermediate_squares = []
    
    def __str__(self):
        return f"Chess path for {self.piece} to {self.land}"
    
    def validate_path(piece, start, land):
        if start == land:
            return False, []
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
                if piece.power.side == Side.WHITE:
                    if drank == 1 and abs(dfile) <= 1:
                        valid = True
                    elif start.rank < 2 and drank == 2 and dfile == 0:
                        intermediate_squares.append(Square(rank=start.rank + 1, file=start.file))
                        valid = True
                elif piece.power.side == Side.BLACK:
                    if drank == -1 and abs(dfile) <= 1:
                        valid = True
                    elif start.rank >= 6 and drank == -2 and dfile == 0:
                        intermediate_squares.append(Square(rank=start.rank - 1, file=start.file))
                        valid = True
            case _:
                pass
        return valid, intermediate_squares