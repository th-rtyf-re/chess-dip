# -*-coding:utf8-*-

from enum import IntEnum

from chessdip.board.square import Square

class Side(IntEnum):
    NEUTRAL = 0
    WHITE = 1
    BLACK = 2

class Power:
    def __init__(self, name, palette, side, d_king=False):
        self.name = name
        if side == Side.WHITE:
            self.piece_color = (palette.white, palette.neutral) # tuple: fc, highlight
        elif side == Side.BLACK:
            self.piece_color = (palette.neutral, palette.black)
        else:
            self.piece_color = (palette.neutral, palette.neutral)
        self.square_color = (palette.dark, palette.light) # tuple: dark, light
        self.path_color = palette.neutral
        self.side = side
        self.d_king = d_king
    
    def __str__(self):
        return self.name
    
    def get_king_square(self):
        file = 3 if self.d_king else 4 # d else e
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)
    
    def get_king_rook_square(self):
        file = 0 if self.d_king else 7 # a else h
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)
    
    def get_queen_rook_square(self):
        file = 7 if self.d_king else 0 # h else a
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)
    
    def get_kingside_castle_king_square(self):
        file = 1 if self.d_king else 6 # b else g
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)
    
    def get_kingside_castle_rook_square(self):
        file = 2 if self.d_king else 5 # c else f
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)
    
    def get_queenside_castle_king_square(self):
        file = 5 if self.d_king else 2 # f else c
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)
    
    def get_queenside_castle_rook_square(self):
        file = 4 if self.d_king else 3 # e else d
        rank = 0 if self.side == Side.WHITE else 7
        return Square(file=file, rank=rank)