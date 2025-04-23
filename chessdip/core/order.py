# -*-coding:utf8-*-

from chessdip.board.chess_path import ChessPath

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
    
    def __init__(self, piece, *other_args, virtual=False):
        self.piece = piece
        self.other_args = other_args
        self.virtual = virtual
        
        self.supports = []
        self.convoys = []
        self.supported_order = None
        self.convoyed_order = None
        
        self.success = True
    
    def __str__(self):
        pass
    
    def get_piece(self):
        return self.piece
    
    def get_virtual(self):
        return self.virtual
    
    def set_virtual(self, virtual=True):
        self.virtual = virtual
    
    def get_supports(self):
        return self.supports
    
    def add_support(self, support_order):
        self.supports.append(support_order)
    
    def remove_support(self, support_order):
        self.supports.remove(support_order)
    
    def get_convoys(self):
        return self.convoys

    def add_convoy(self, convoy_order):
        self.convoys.append(convoy_order)
    
    def remove_convoy(self, convoy_order):
        self.convoys.remove(convoy_order)
    
    def set_convoys(self, convoys):
        self.convoys = convoys
    
    def get_supported_order(self):
        return self.supported_order
    
    def get_convoyed_order(self):
        return self.convoyed_order
    
    def set_convoyed_order(self, order):
        self.convoyed_order = order
    
    def get_args(self):
        return (self.piece,) + self.other_args
    
    def get_intermediate_squares(self):
        return []
    
    def is_inheritable(self, *args):
        return False
    
    def execute(self, board, console):
        return False
    
    def set_success(self, success):
        self.success = success
    
    def get_success(self):
        return self.success
    
    def evaluate(self):
        pass
    
class HoldOrder(Order):
    def __init__(self, piece, virtual=False):
        super().__init__(piece, virtual=virtual)
        
        self.chess_path = ChessPath(piece, piece.square)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} hold"
    
    def get_starting_square(self):
        return self.piece.square
    
    def get_landing_square(self):
        return self.piece.square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.piece} failed to hold.")
            return False
        console.out(f"{self.piece} held.")
        return True

class MoveOrder(Order):
    def __init__(self, piece, landing_square, virtual=False):
        super().__init__(piece, landing_square, virtual=virtual)
        
        self.landing_square = landing_square
        self.chess_path = ChessPath(piece, self.landing_square)
        
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} move to {self.landing_square}"
    
    def get_starting_square(self):
        return self.piece.square
    
    def get_landing_square(self):
        return self.landing_square
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.piece} failed to move.")
            return False
        elif not self.chess_path.valid:
            console.out(f"{self.piece} cannot move to {self.landing_square}.")
            return False
        # other_piece = board.get_piece(self.landing_square)
        # if other_piece is not None:
        #     board.remove_piece(other_piece)
        board.move_piece_to(self.piece, self.landing_square)
        board.set_ownership(self.landing_square, self.piece.power)
        console.out(f"{self.piece} moved to {self.landing_square}.")
        return True

class ConvoyOrder(Order):
    def __init__(self, piece, square, convoyed_order, virtual=False):
        """
        piece should be None
        """
        super().__init__(piece, square, convoyed_order, virtual=virtual)
        
        self.square = square
        self.convoyed_order = convoyed_order
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.square} convoy {self.convoyed_order}"
    
    def get_landing_square(self):
        return self.square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.square} failed to convoy {self.convoyed_order}.")
            return False
        elif self.square in self.convoyed_order.get_intermediate_squares():
            console.out(f"{self.square} convoyed {self.convoyed_order}.")
            return True
        console.out(f"{self.square} cannot support {self.convoyed_order}.")
        return False

class SupportOrder(Order):
    def __init__(self, piece, supported_square, virtual=False):
        super().__init__(piece, supported_square, virtual=virtual)
        
        self.supported_square = supported_square
        self.chess_path = ChessPath(piece, supported_square)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} generic support {self.supported_square}"
    
    def get_args(self):
        """
        Manual overwrite
        """
        return (self.piece, self.supported_square)
    
    def get_starting_square(self):
        return self.piece.square
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def is_inheritable(self, piece, support_arg):
        try:
            return piece == self.piece and support_arg.get_landing_square() == self.supported_square
        except AttributeError:
            return piece == self.piece and support_arg == self.supported_square

class SupportHoldOrder(SupportOrder):
    def __init__(self, piece, supported_order, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_args(self):
        return (self.piece, self.supported_order)
    
    def get_landing_square(self):
        return self.supported_square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.piece} failed to support {self.supported_order}.")
            return False
        elif not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportMoveOrder(SupportOrder):
    def __init__(self, piece, supported_order, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_args(self):
        return (self.piece, self.supported_order)
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def get_landing_square(self):
        return self.supported_square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.piece} failed to support {self.supported_order}.")
            return False
        elif not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class SupportConvoyOrder(SupportOrder):
    def __init__(self, piece, supported_order, virtual=False):
        super(SupportOrder, self).__init__(piece, supported_order, virtual=virtual)
        
        self.supported_order = supported_order
        self.supported_square = self.supported_order.get_landing_square()
        self.chess_path = ChessPath(piece, self.supported_square)
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_order}"
    
    def get_args(self):
        return (self.piece, self.supported_order)
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def get_landing_square(self):
        return self.supported_square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.piece} failed to support {self.supported_order}.")
            return False
        elif not self.chess_path.valid:
            console.out(f"{self.piece} cannot support {self.supported_order}.")
            return False
        console.out(f"{self.piece} supported {self.supported_order}.")
        return True

class BuildOrder(Order):
    def __init__(self, power, piece_code, square, virtual=False):
        super().__init__(None, virtual=virtual)
        
        self.power = power
        self.piece_code = piece_code
        self.square = square
            
    def __str__(self):
        names = ["Pawn", "Knight", "Bishop", "Rook", "King"]
        return f"{self.power} build {names[self.piece_code]} on {self.square}"
    
    def execute(self, board, console):
        board.vacate_square(self.square)
        piece = board.add_piece(self.piece_code, self.power, self.square)
        console.out(f"{self.power} built {piece}.")
        return piece

class DisbandOrder(Order):
    def __init__(self, piece, virtual=False):
        super().__init__(piece, virtual=virtual)
        
    def __str__(self):
        return f"{self.piece} disband"
    
    def execute(self, board, console):
        board.remove_piece(self.piece)
        console.out(f"{self.piece} disbanded.")
        return True