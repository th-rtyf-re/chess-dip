# -*-coding:utf8-*-

class Piece:
    """
    Playable pieces. Piece types are identified by integers. The available
    pieces are pawns (0), knights (1), bishops (2), rooks (3), and kings (4).
    """
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    KING = 4
    
    def __init__(self, code, power, square):
        self.code = code
        self.power = power
        self.square = square
    
    def __str__(self):
        names = ["Pawn", "Knight", "Bishop", "Rook", "King"]
        return f"{self.power} {names[self.code]} at {self.square}"
    
    def get_power(self):
        return self.power
    
    def get_square(self):
        return self.square
    
    def move_to(self, square):
        self.square = square
    
    def remove(self):
        pass