# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from power import Power
from square import Square
from piece import Piece
from board import *
from visualizer import Visualizer
from chess_path import *
from order import *
from order_artists import *
from parser import *

class Console:
    def __init__(self):
        pass
    
    def out(self, *args, **kwargs):
        print(*args, **kwargs)
    
    def input(self, *args, **kwargs):
        return input(*args, **kwargs)

class OrderManager:
    """
    Managing orders and their artists
    """
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.artists = {}
        
        self.order_subclasses = {
            Order.HOLD: HoldOrder,
            Order.MOVE: MoveOrder,
            Order.CONVOY: ConvoyOrder,
            Order.SUPPORT: SupportOrder,
            Order.SUPPORT_HOLD: SupportHoldOrder,
            Order.SUPPORT_MOVE: SupportMoveOrder,
            Order.SUPPORT_CONVOY: SupportConvoyOrder,
            Order.BUILD: BuildOrder,
            Order.DISBAND: DisbandOrder
        }
    
    def has_orders(self):
        return bool(self.artists)
    
    def get_orders(self):
        return self.artists.keys()
    
    def get_items(self):
        return self.artists.items()
    
    def clear(self):
        self.artists.clear()
    
    def add(self, order):
        supported_order = order.get_supported_order()
        supported_artist = None
        if supported_order is not None:
            supported_artist = self.artists[supported_order]
        order_artist = self.visualizer.make_order_artist(order, supported_artist)
        self.artists[order] = order_artist
        self.visualizer.add_artist(order_artist)
        return order
    
    def remove(self, order):
        self.artists[order].remove() # From visualizer
        del self.artists[order]
        self.visualizer.set_stale()
    
    def set_virtual(self, order, virtual=True):
        order.set_virtual(virtual)
        self.artists[order].set_virtual(virtual)
        for convoy_order in order.get_convoys():
            self.set_virtual(convoy_order, virtual)
        self.visualizer.set_stale()
    
    def add_support(self, order, support_order):
        order.add_support(support_order)
        self.artists[order].add_support(self.artists[support_order])
        self.visualizer.set_stale()
    
    def remove_support(self, order, support_order):
        order.remove_support(support_order)
        self.artists[order].remove_support(self.artists[support_order])
        self.visualizer.set_stale()
    
    def add_convoy(self, order, convoy_order):
        order.add_convoy(convoy_order)
    
    def remove_convoy(self, order, convoy_order):
        order.remove_convoy(convoy_order)
    
    def inherit_convoys(self, order, other_order):
        convoys = other_order.get_convoys()
        order.set_convoys(convoys)
        for convoy_order in convoys:
            convoy_order.set_convoyed_order(order)
            convoy_order.set_virtual(order.get_virtual())
    
    def retract(self, order):
        # If supported by a real order, keep but make virtual
        for support_order in order.get_supports():
            if not support_order.get_virtual():
                self.set_virtual(order)
                return
        
        # If supporting an order, update the supported order's support list.
        supported_order = order.get_supported_order()
        if supported_order is not None:
            self.remove_support(supported_order, order)
            # If supported order is virtual, try removing that order as well
            if supported_order.get_virtual():
                self.retract(supported_order)
        
        # If convoyed by a supported convoy order, keep in some sense
        for convoy_order in order.get_convoys():
            if convoy_order.get_supports():
                # If order is a support, convert into generic support
                if isinstance(order, SupportOrder):
                    generic_support_order = SupportOrder(order.piece, order.supported_square, virtual=True)
                    self.inherit_convoys(generic_support_order, order)
                    self.remove(order)
                    self.add(generic_support_order)
                else: # Move order: make virtual
                    order.set_virtual()
                return
        
        # If convoying an order, try to retract the convoyed order: if that
        # succeeds, then order will also be removed.
        convoyed_order = order.get_convoyed_order()
        if convoyed_order is not None:
            self.retract(convoyed_order)
            return
        
        # Finally, remove order and all convoys
        self.remove(order)
        for convoy_order in order.get_convoys():
            self.remove(convoy_order)
        return
    
    def get_order(self, order_code, args, virtual=False):
        """
        args is what is used to construct the order.
        """
        order_subclass = self.order_subclasses[order_code]
        # find matching order
        inheritable_order = None
        for other_order in self.get_orders():
            if isinstance(other_order, order_subclass) and args == order_subclass.get_args(other_order):
                # found matching order
                order = other_order
                self.set_virtual(order, order.get_virtual() and virtual)
                return order
            elif type(other_order) is SupportOrder and issubclass(order_subclass, SupportOrder) and other_order.is_inheritable(*args):
                # found inheritable order
                inheritable_order = other_order
                break
        if inheritable_order is not None:
            order = order_subclass(*args, virtual=virtual)
            self.inherit_convoys(order, other_order)
            self.remove(inheritable_order)
            self._clear_conflicting_orders(order)
            self.add(order)
            return order
        else:
            # no match: make new order
            order = order_subclass(*args, virtual=virtual)
            self._clear_conflicting_orders(order)
            self.add(order)
            self.add_convoys(order)
            return order
    
    def _clear_conflicting_orders(self, order):
        """
        Does not work for clearing convoy orders, although this function
        should never be used for that
        """
        conflicting_orders = []
        for other_order in self.get_orders():
            if other_order.get_piece() == order.get_piece() and not other_order.get_virtual() and not order.get_virtual():
                conflicting_orders.append(other_order)
        for order in conflicting_orders:
            self.retract(order)
    
    def add_convoys(self, order):
        """
        This is the only place where convoys are added. Note that we do not
        check for conflicting orders.
        """
        for square in order.get_intermediate_squares():
            convoy_order = ConvoyOrder(None, square, order, virtual=order.virtual)
            self.add(convoy_order)
            self.add_convoy(order, convoy_order)
    
    def get_support_order(self, order_code, piece, supported_order_code, supported_order_args, virtual=False):
        supported_order = self.get_order(supported_order_code, supported_order_args, virtual=True)
        order = self.get_order(order_code, (piece, supported_order), virtual=virtual)
        self.add_support(supported_order, order)
        return order
    
    def get_support_convoy_order(self, piece, convoy_square, convoyed_order_code, convoyed_order_args, virtual=False):
        convoyed_order = self.get_order(convoyed_order_code, convoyed_order_args, virtual=True)
        convoy_order = self.get_order(Order.CONVOY, (None, convoy_square, convoyed_order), virtual=True)
        order = self.get_order(Order.SUPPORT_CONVOY, (piece, convoy_order), virtual=virtual)
        self.add_support(convoy_order, order)
        return order

class BoardManager:
    """
    Squares, supply centers, and pieces. Should have the same signature as
    a Board object
    """
    def __init__(self, powers, visualizer):
        self.visualizer = visualizer
        
        self.board = Board(powers)
        self.board_artist = BoardArtist(self.board)
        self.visualizer.add_artist(self.board_artist)
        
        self.piece_artists = {}
    
    def get_pieces(self):
        return self.piece_artists.keys()
    
    def add_piece(self, code, power, square):
        piece = Piece(code, power, square)
        self.set_ownership(square, power)
        piece_artist = self.visualizer.make_piece_artist(piece)
        self.piece_artists[piece] = piece_artist
        self.visualizer.add_artist(piece_artist)
        return piece
    
    def remove_piece(self, piece):
        self.piece_artists[piece].remove()
        del self.piece_artists[piece]
        self.visualizer.set_stale()
    
    def get_piece(self, square):
        for piece in self.get_pieces():
            if piece.get_square() == square:
                return piece
        return None
    
    def set_ownership(self, square, power):
        changed = self.board.set_ownership(square, power)
        if changed:
            self.board_artist.set_owner(square, power)
            self.visualizer.set_stale()
    
    def set_sc_ownership(self, square, power):
        changed = self.board.set_sc_ownership(square, power)
        if changed:
            self.board_artist.set_sc_owner(square, power)
            self.visualizer.set_stale()
    
    def vacate_square(self, square):
        for piece in self.get_pieces():
            if piece.get_square() == square:
                self.remove_piece(piece)
                self.visualizer.set_stale()
    
    def move_piece_to(self, piece, square):
        piece.move_to(square)
        self.piece_artists[piece].move_to(square)
        self.set_ownership(square, piece.get_power())
        self.visualizer.set_stale()

class GameManager:
    def __init__(self, powers=None):
        if powers is None:
            self.powers = []
        else:
            self.powers = powers
        self.visualizer = Visualizer()
        self.order_manager = OrderManager(self.visualizer)
        self.console = Console()
        self.board = BoardManager(self.powers, self.visualizer)
        self.parser = Parser(Order)
        
        self.piece_dict = {
            'P': Piece.PAWN,
            'N': Piece.KNIGHT,
            'B': Piece.BISHOP,
            'R': Piece.ROOK,
            'K': Piece.KING
        }
    
    def update_view(self):
        self.visualizer.render()
    
    def setup_pieces(self, power, notations):
        for notation in notations:
            instruc = notation.replace(" ", "")
            piece_code = self.piece_dict[instruc[0]]
            square = self._square(instruc[1:3])
            self.board.add_piece(piece_code, power, square)
    
    def _get_power(self, power_name):
        """
        power_name is assumed lowercase
        """
        for power in self.powers:
            full_name = power.name.lower()
            if len(power_name) <= len(full_name) and full_name[:len(power_name)] == power_name:
                return power
        raise ValueError(f"Could not find power {power_name}!")
    
    def _find_order_on_square(self, square, virtual=None):
        piece = self.board.get_piece(square)
        if piece is not None:
            for order in self.order_manager.get_orders():
                if order.get_piece() == piece:
                    if virtual is None:
                        return order
                    elif order.get_virtual() == virtual:
                        return order
        return None
    
    def progress(self):
        for order, artist in self.order_manager.get_items():
            if not order.get_virtual():
                order.execute(self.board, self.console)
            artist.remove()
        self.order_manager.clear()
        self.visualizer.set_stale()
    
    def _square(self, square_str):
        """
        Assume that `square_str` is a valid input.
        """
        if len(square_str) < 2:
            return None
        file = ord(square_str[0]) - ord('a')
        rank = int(square_str[1]) - 1
        return Square(file=file, rank=rank)
    
    def process_orders(self, power, messages):
        for message in messages:
            self._process_order(power, message.lower().replace(' ', ''))
    
    def _process_order(self, power, message):
        """
        Currently written for the sandbox mode, but should be adapted.
        
        We allow orders along illegal chess paths, but we do not allow
        illegal implicit convoy orders.
        """
        order_code, args = self.parser.parse(message)
        if order_code is None:
            self.console.out("Could not parse order.")
            return False
        
        starting_square = self._square(args[0])
        piece = self.board.get_piece(starting_square)
        if order_code == Order.BUILD:
            pass
        elif piece is None:
            self.console.out(f"No piece on {starting_square}.")
            return False
        elif piece.power != power:
            self.console.out("Cannot order another power's piece.")
            return False
        
        match order_code:
            case Order.HOLD:
                self.order_manager.get_order(order_code, (piece,))
                return True
            case Order.MOVE:
                landing_square = self._square(args[1])
                self.order_manager.get_order(order_code, (piece, landing_square))
                return True
            case Order.SUPPORT_HOLD:
                supported_square = self._square(args[1])
                supported_piece = self.board.get_piece(supported_square)
                self.order_manager.get_support_order(order_code, piece, Order.HOLD, (supported_piece,))
                return True
            case Order.SUPPORT_MOVE:
                supported_square = self._square(args[1])
                supported_piece = self.board.get_piece(supported_square)
                supported_landing_square = self._square(args[3])
                self.order_manager.get_support_order(order_code, piece, Order.MOVE, (supported_piece, supported_landing_square))
                return True
            case Order.SUPPORT_CONVOY:
                convoy_square = self._square(args[1])
                convoy_starting_square = self._square(args[2])
                convoyed_piece = self.board.get_piece(convoy_starting_square)
                convoyed_order_code = Order.SUPPORT if args[3] == 's' else Order.MOVE
                convoy_landing_square = self._square(args[4])
                _, intermediate_squares = ChessPath.validate_path(convoyed_piece, convoy_starting_square, convoy_landing_square)
                if convoy_square not in intermediate_squares:
                    self.console.out("Convoying square cannot convoy along specified path.")
                    return False
                self.order_manager.get_support_convoy_order(piece, convoy_square, convoyed_order_code, (convoyed_piece, convoy_landing_square))
                return True
            case Order.BUILD:
                piece_chr = args[1].upper() if args[1] else "P"
                piece_code = self.piece_dict[piece_chr]
                order = BuildOrder(power, piece_code, starting_square)
                self.order_manager._clear_conflicting_orders(order)
                self.order_manager.add(order)
                return True
            case Order.DISBAND:
                order = DisbandOrder(piece)
                self.order_manager._clear_conflicting_orders(order)
                self.order_manager.add(order)
                return True
            case _:
                self.console.out("Unknown error!")
                return False
    
    def sandbox(self):
        self.console.out("Beginning sandbox. Awaiting instructions.")
        power = None
        self.visualizer.ion()
        self.visualizer.show()
        while True:
            self.visualizer.render()
            message = self.console.input("> ").lower().replace(' ', '')
            
            if message in ["exit", "quit"]:
                return
            elif message in ["help"]:
                self.console.out("Type \"power\" to specify your power. Type \"build\" to build. Type \"exit\" or \"quit\" to exit.")
            elif message == "orders":
                if not self.order_manager.has_orders():
                    self.console.out("No orders to display.")
                else:
                    self.console.out("Current orders:")
                    for order in self.order_manager.get_orders():
                        self.console.out(order)
            elif message == "progress":
                self.progress()
            elif message[:len("power")] == "power":
                power_str = message[len("power"):]
                try:
                    power = self._get_power(power_str)
                    self.console.out(f"Playing as {power}.")
                except ValueError:
                    self.console.out(f"Power {power_str} not found.")
            elif message[:len("remove")] == "remove":
                square = self._square(message[len("remove"):])
                if square is None:
                    continue
                order = self._find_order_on_square(square, virtual=False)
                if order is not None:
                    self.order_manager.retract(order)
            elif message[:len("save")] == "save":
                filename = message[len("save"):]
                if not filename:
                    filename = "render.png"
                elif '.' not in filename:
                    filename += ".png"
                plt.savefig(filename, dpi=300)
            elif power is None:
                self.console.out("No power has been selected. Select a power by writing \"power [name]\"")
            else: # Message is an order
                self._process_order(power, message)


if __name__ == "__main__":
    color_dict = {
        "opal": ("honeydew", "limegreen"),
        "quartz": ("mistyrose", "darkred"),
        "obsidian": ("royalblue", "k"),
        "onyx": ("goldenrod", "k"),
        "black": ("k", "k"),
        "white": ("w", "w"),
        "none": ("none", "k")
    }
    powers = [
        Power(0, "neutral", color_dict["none"], ((175/255, 138/255, 105/255), (237/255, 218/255, 185/255)), 0),
        Power(1, "England", color_dict["quartz"], ("indianred", "lightsalmon"), -1),
        Power(2, "Italy", color_dict["opal"], ("forestgreen", "lightgreen"), -1),
        Power(3, "France", color_dict["obsidian"], ("steelblue", "lightskyblue"), -2),
        Power(4, "Scandinavia", color_dict["onyx"], ("darkgoldenrod", "palegoldenrod"), -2),
        Power(-2, "black", color_dict["black"], ("k", "k"), -2),
        Power(-1, "white", color_dict["white"], ("w", "w"), -1),
    ]
    GM = GameManager(powers)
    GM.setup_pieces(powers[1], ["K d1", "P c2", "N b1", "Ra1"])
    GM.setup_pieces(powers[2], ["K e1", "P e2", "B f1", "Rh1"])
    GM.setup_pieces(powers[3], ["K e8", "P e7", "N g8", "Rh8"])
    GM.setup_pieces(powers[4], ["K d8", "P d7", "B c8", "Ra8"])
    
    # GM.process_orders(powers[2], ["f1sh3ch1sh8", "h1sh8h"])
    GM.sandbox()
    
