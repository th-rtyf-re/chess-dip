# -*-coding:utf8-*-

from enum import IntEnum

class Side(IntEnum):
    NEUTRAL = 0
    WHITE = -1
    BLACK = -2

class Power:
    def __init__(self, code, name, piece_color, square_color, side):
        self.code = code
        self.name = name
        self.piece_color = piece_color# tuple: fc, highlight
        self.square_color = square_color# tuple: dark, light
        self.side = side# 0 for neutral, -1 for white, -2 for black
    
    def __str__(self):
        return self.name
    
    def get_code(self):
        return self.code