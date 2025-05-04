# -*-coding:utf8-*-

from chessdip.board.chess_path import ChessPath
from chessdip.board.piece import Piece

class Order:
    """
    Base class for orders. Orders can be real or virtual, as indicated by
    the optional argument `virtual`. Virtual orders are orders that have not
    been ordered themselves, but that are supported or convoyed by other
    orders.
    """
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
    
    def short_str(self):
        """
        String representation called by convoys. This is separate from the
        usual `__str__` method to prevent infinite recursion.
        """
        return self.__str__()
    
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
        """
        Get arguments used to initialize the order.
        """
        return (self.piece,) + self.other_args
    
    def get_intermediate_squares(self):
        return []
    
    def is_inheritable(self, *args):
        """
        Check if the order can be inherited by another order with the
        arguments `args`.
        """
        return False
    
    def execute(self, board, console):
        """
        Execute the order.
        
        Parameters:
        ----------
        - board: BoardInterface. Interface that manages the board and the
            pieces.
        - console: Console. Place where messages are sent.
        
        Returns:
        -------
        - bool. True if the order succeeds, and False if not.
        """
        return False
    
    def set_success(self, success):
        self.success = success
    
    def get_success(self):
        return self.success
    
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
    """
    Class for all move orders. The distinction between attack and travel
    orders is handled by the attribute `move_type`, which takes one of three
    values: MOVE (0), corresponding to a move that is both an attack and a
    travel, ATTACK (1), and TRAVEL (2).
    """
    MOVE = 0
    ATTACK = 1
    TRAVEL = 2
    
    def __init__(self, piece, landing_square, virtual=False, move_type=MOVE, exception=None):
        """
        Parameters:
        ----------
        - piece: Piece.
        - landing_square: Square.
        - virtual: bool, optional. Default value is False.
        - move_type: int, optional. Default value is 0, corresponding to a
            regular move.
        - exception: str, optional. This argument indicates an exceptional
            move, such as a castle or en passant move. This argument is
            passed on to the ChessPath. Default value is None.
        """
        super().__init__(piece, landing_square, virtual=virtual)
        
        self.landing_square = landing_square
        self.chess_path = ChessPath(piece, self.landing_square, exception=exception)
        self.move_type = move_type
        
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} move to {self.landing_square}"
    
    def get_starting_square(self):
        return self.piece.square
    
    def get_landing_square(self):
        return self.landing_square
    
    def get_intermediate_squares(self):
        return self.chess_path.intermediate_squares
    
    def is_attack(self):
        return self.move_type == MoveOrder.ATTACK
    
    def is_travel(self):
        return self.move_type == MoveOrder.TRAVEL
    
    def execute(self, board, console):
        verb = ["move", "attack", "travel"][self.move_type]
        if self.virtual:
            return False
        elif not self.success:
            console.out(f"{self.piece} failed to {verb}.")
            return False
        elif not self.chess_path.valid:
            console.out(f"{self.piece} cannot {verb} to {self.landing_square}.")
            return False
        # Successful move
        if self.piece.code == Piece.PAWN and self.is_attack() and board.get_piece(self.landing_square) is None:
            console.out(f"{self.piece} successfully attacked, but does not move to, {self.landing_square}.")
            return True
        
        if not self.is_attack():
            board.move_piece_to(self.piece, self.landing_square)
            board.set_ownership(self.landing_square, self.piece.power)
        if self.piece.code == Piece.PAWN and self.get_intermediate_squares():
            board.mark_en_passant(self.piece, self.get_intermediate_squares()[0]) 
        console.out(f"{self.piece} moved to {self.landing_square}.")
        return True

class ConvoyOrder(Order):
    def __init__(self, piece, square, convoyed_order, virtual=False):
        """
        Parameters:
        ----------
        - piece: None. This argument is just here for consistency with the
            parent class.
        - square: Square.
        - convoyed_order: Order. A move or support order.
        - virtual: bool, optional. Default value is False.
        """
        super().__init__(piece, square, convoyed_order, virtual=virtual)
        
        self.square = square
        self.convoyed_order = convoyed_order
    
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.square} convoy {self.convoyed_order.short_str()}"
    
    def get_starting_square(self):
        return self.square
    
    def get_landing_square(self):
        return self.square
    
    def execute(self, board, console):
        if self.virtual:
            return False
        elif not self.success:
            # console.out(f"{self.square} failed to convoy {self.convoyed_order}.")
            return False
        elif self.square in self.convoyed_order.get_intermediate_squares():
            # console.out(f"{self.square} convoyed {self.convoyed_order}.")
            return True
        # console.out(f"{self.square} cannot support {self.convoyed_order}.")
        return False

class SupportOrder(Order):
    """
    Parent class for all support orders.
    """
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
    
    def short_str(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_square}"
    
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
    
    def short_str(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_square}"
    
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
    
    def short_str(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} support {self.supported_square}"
    
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

class OrderLinker:
    """
    Class managing a set of linked orders, that is, orders whose success
    depends on the success of the others.
    
    This class shares the get/set success methods of `Order`, making it
    equivalent in the view of the adjudicator.
    """
    def __init__(self, orders=None):
        if orders is None:
            orders = []
        self.orders = orders
        
        self.success = False
    
    def __str__(self):
        return f"Linker for: " + ", ".join([str(order) for order in self.orders])
    
    def get_orders(self):
        return self.orders
    
    def set_orders(self, orders):
        self.orders = orders
    
    def add_order(self, order):
        self.orders.append(order)
    
    def remove_order(self, order):
        if order in self.orders:
            self.orders.remove(order)
    
    def get_success(self, success):
        return self.success
    
    def set_success(self, success):
        self.success = success

class LinkedOrder:
    """
    Base class for linked orders.
    """
    def __init__(self, linker):
        self.linker = linker
        self.linker.add_order(self)
    
    def get_linker(self):
        return self.linker
    
    def set_virtual(self, virtual):
        for order in self.linker.get_orders():
            super(LinkedOrder, order).set_virtual(virtual)

class LinkedMoveOrder(LinkedOrder, MoveOrder):
    """
    Class for linked move orders.
    """
    def __init__(self, linker, piece, landing_square, virtual=False, move_type=MoveOrder.MOVE, exception=None):
        MoveOrder.__init__(self, piece, landing_square, virtual=virtual, move_type=move_type, exception=exception)
        LinkedOrder.__init__(self, linker)
        
    def __str__(self):
        prefix = "[virtual] " if self.virtual else ""
        return prefix + f"{self.piece} linked move to {self.landing_square}"

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