# -*-coding:utf8-*-

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np

from piece import *
from chess_path import *

class Order:
    HOLD = 0
    MOVE = 1
    CONVOY = 2
    SUPPORT = 6
    SUPPORT_HOLD = 3
    SUPPORT_MOVE = 4
    SUPPORT_CONVOY = 5
    BUILD = -1
    DISBAND = -2
    
    support_order_codes = {
        SUPPORT_HOLD: HOLD,
        SUPPORT_MOVE: MOVE,
        SUPPORT_CONVOY: CONVOY
    }
    
    def __init__(self, piece, *other_args, visualizer=None, remove_method=None, virtual=False):
        self.piece = piece
        self.other_args = other_args
        self.visualizer = visualizer
        self._full_remove_method = remove_method
        self.virtual = virtual
        
        self.supports = []
        self.convoys = []
        self.supported_order = None
        self.convoyed_order = None
    
    def __str__(self):
        pass
    
    def get_args(self):
        return (self.piece,) + self.other_args
    
    def get_intermediate_squares(self):
        return []
    
    def is_inheritable(self, *args):
        return False
    
    def get_piece(self):
        return self.piece
    
    def execute(self, board, console):
        return False
    
    def set_virtual(self, virtual=True):
        self.virtual = virtual
        self.artist.set_virtual(virtual)
        for convoy_order in self.convoys:
            convoy_order.set_virtual(virtual)
    
    def add_support(self, support_order):
        self.supports.append(support_order)
        self.visualizer.add_support(self, support_order)
    
    def remove_support(self, support_order):
        self.supports.remove(support_order)
        self.artist.remove_support(support_order)
    
    def add_convoy(self, convoy_order):
        self.convoys.append(convoy_order)
    
    def remove_convoy(self, convoy_order):
        self.convoys.remove(convoy_order)
    
    def inherit_convoys(self, other_order):
        self.convoys = other_order.convoys
        for convoy in self.convoys:
            convoy.convoyed_order = self
            convoy.set_virtual(self.virtual)

class HoldOrder(Order):
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.chess_path = ChessPath(piece, piece.square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} hold"
    
    def get_landing_square(self):
        return self.piece.square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        console.out(f"{self.piece} held.")
        return True

class MoveOrder(Order):
    def __init__(self, piece, landing_square, visualizer, remove_method, virtual=False):
        super().__init__(piece, landing_square, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.landing_square = landing_square
        self.chess_path = ChessPath(piece, self.landing_square)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} move to {self.landing_square}"
    
    def get_landing_square(self):
        return self.landing_square
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot move to {self.landing_square}.")
            return False
        other_piece = board.get_piece(self.landing_square)
        if other_piece is not None:
            board.remove_piece(other_piece)
        board.move_piece_to(self.piece, self.landing_square)
        board.set_ownership(self.landing_square, self.piece.power)
        console.out(f"{self.piece} moved to {self.landing_square}.")
        return True

class ConvoyOrder(Order):
    def __init__(self, piece, square, convoyed_order, visualizer, remove_method, virtual=False):
        """
        piece should be None
        """
        super().__init__(piece, square, convoyed_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.square = square
        self.convoyed_order = convoyed_order
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.square} convoy {self.convoyed_order}"
    
    def get_landing_square(self):
        return self.square
    
    def execute(self, board, console):
        if self.square in self.convoyed_order.get_intermediate_squares():
            console.out(f"{self.square} convoyed {self.convoyed_order}.")
            return True
        console.out(f"{self.square} cannot support {self.convoyed_order}.")
        return False
    
    def update_convoyed_order(self, new_order):# because it can change!
        self.convoyed_order = new_order

class SupportOrder(Order):
    def __init__(self, piece, supported_square, visualizer, remove_method, virtual=False):
        super().__init__(piece, supported_square, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_square = supported_square
        self.chess_path = ChessPath(piece, supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} generic support {self.supported_square}"
    
    def get_args(self):
        """
        Manual overwrite
        """
        return (self.piece, self.supported_square)
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def is_inheritable(self, piece, supported_order):
        return piece == self.piece and supported_order.get_landing_square() == self.supported_square

class SupportHoldOrder(SupportOrder):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportMoveOrder(SupportOrder):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportConvoyOrder(SupportOrder):
    def __init__(self, piece, supported_order, visualizer, remove_method, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def execute(self, board, console):
        if not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class BuildOrder(Order):
    def __init__(self, power, piece_code, square, visualizer, remove_method, virtual=False):
        super().__init__(None, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.power = power
        self.piece_code = piece_code
        self.square = square
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        names = ["Pawn", "Knight", "Bishop", "Rook", "King"]
        return f"{self.power} build {names[self.piece_code]} on {self.square}"
    
    def execute(self, board, console):
        board.vacate_square(self.square)
        piece = board.add_piece(self.piece_code, self.power, self.square)
        console.out(f"{self.power} built {piece}.")
        return piece

class DisbandOrder(Order):
    def __init__(self, piece, visualizer, remove_method, virtual=False):
        super().__init__(piece, visualizer=visualizer, remove_method=remove_method, virtual=virtual)
        
        self.artist = self.visualizer.make_order_artist(self)
    
    def __str__(self):
        return f"{self.piece} disband"
    
    def execute(self, board, console):
        board.remove_piece(self.piece)
        console.out(f"{self.piece} disbanded.")
        return True