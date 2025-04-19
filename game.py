# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from power import Power
from square import Square
from piece import Piece
from board import Board
from visualizer import Visualizer
from chess_path import *
from order import *
from parser import *

class Console:
    def __init__(self):
        pass
    
    def out(self, *args, **kwargs):
        print(*args, **kwargs)
    
    def input(self, *args, **kwargs):
        return input(*args, **kwargs)

class GameManager:
    def __init__(self, powers=None):
        if powers is None:
            self.powers = []
        else:
            self.powers = powers
        self.visualizer = Visualizer()
        self.console = Console()
        self.board = Board(self.powers, self.visualizer)
        self.orders = []# including virtual orders and convoy orders, I guess
        self.parser = Parser(Order)
        
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
    
    def update_view(self):
        self.visualizer.render()
    
    def setup_pieces(self, notations, power_name):
        for notation in notations:
            instruc = notation.replace(" ", "")
            piece_code = Piece.piece_dict[instruc[0]]
            square = self._square(instruc[1:3])
            power = self._get_power(power_name)
            self.board.add_piece(piece_code, power, square)
    
    def _get_power(self, power_name):
        for power in self.powers:
            full_name = power.name.lower()
            if len(power_name) <= len(full_name) and full_name[:len(power_name)] == power_name.lower():
                return power
        raise ValueError(f"Could not find power {power_name}!")
    
    def find_order(self, piece, order_code=None, virtual=None):
        for order in self.orders:
            if ((order_code is None or isinstance(order, self.order_subclasses[order_code]))
                and order.piece == piece):
                if virtual is None:
                    return order
                elif order.virtual == virtual:
                    return order
        return None
    
    def find_order_on_square(self, square, order_code=None, virtual=None):
        piece = self.board.get_piece(square)
        if piece is not None:
            return self.find_order(piece, order_code=order_code, virtual=virtual)
        return None
    
    def add_order(self, order):
        self.orders.append(order)
        self.visualizer.add_order(order)
    
    def full_remove_order(self, order):
        self.orders.remove(order)
        self.visualizer.erase_order(order)
    
    def retract_order(self, order):
        # If supported by a real order, keep but make virtual
        for support_order in order.supports:
            if not support_order.virtual:
                order.set_virtual()
                return
        
        # If supporting an order, update the supported order's support list.
        if order.supported_order is not None:
            order.supported_order.remove_support(order)
            # If supported order is virtual, try removing that order as well
            if order.supported_order.virtual:
                self.retract_order(order.supported_order)
        
        # If convoyed by a supported convoy order, keep in some sense
        for convoy_order in order.convoys:
            if convoy_order.supports:
                # If order is a support, convert into generic support
                if isinstance(order, SupportOrder):
                    generic_support_order = SupportOrder(order.piece, order.supported_square, order.visualizer, order._full_remove_method, virtual=True)
                    generic_support_order.inherit_convoys(order)
                    self.full_remove_order(order)
                    self.add_order(generic_support_order)
                else: # Move order
                    order.set_virtual()
                return
        
        # If convoying an order, try to retract the convoyed order: if that
        # succeeds, then order will also be removed.
        if order.convoyed_order is not None:
            self.retract_order(order.convoyed_order)
            return
        
        # Finally, remove order and all convoys
        order._full_remove_method(order)
        for convoy_order in order.convoys:
            convoy_order._full_remove_method(convoy_order)
        
        return
    
    def get_order(self, order_code, args, virtual=False):
        """
        args is what is used to construct the order.
        """
        order_subclass = self.order_subclasses[order_code]
        # find matching order
        for other_order in self.orders:
            if isinstance(other_order, order_subclass) and args == order_subclass.get_args(other_order):
                order = other_order
                order.set_virtual(order.virtual and virtual)
                return order
            elif type(other_order) is SupportOrder and issubclass(order_subclass, SupportOrder) and other_order.is_inheritable(*args):
                # found inheritable order
                order = order_subclass(*args, self.visualizer, self.full_remove_order, virtual=virtual)
                order.inherit_convoys(other_order)
                self.full_remove_order(other_order)
                self.clear_conflicting_orders(order)
                self.add_order(order)
                return order
        # no match: make new order
        order = order_subclass(*args, self.visualizer, self.full_remove_order, virtual=virtual)
        self.clear_conflicting_orders(order)
        self.add_order(order)
        self.add_convoys(order)
        return order
    
    def clear_conflicting_orders(self, order):
        for other_order in self.orders:
            if other_order.piece == order.piece and not other_order.virtual and not order.virtual:
                self.retract_order(other_order)
    
    def add_convoys(self, order):
        for square in order.get_intermediate_squares():
            convoy_order = ConvoyOrder(None, square, order, self.visualizer, self.full_remove_order, virtual=order.virtual)
            self.add_order(convoy_order)
            order.add_convoy(convoy_order)
    
    def get_support_order(self, order_code, piece, supported_order_code, supported_order_args, virtual=False):
        supported_order = self.get_order(supported_order_code, supported_order_args, virtual=True)
        order = self.get_order(order_code, (piece, supported_order), virtual=virtual)
        supported_order.add_support(order)
        return order
    
    def get_support_convoy_order(self, piece, convoy_square, convoyed_order_code, convoyed_order_args, virtual=False):
        convoyed_order = self.get_order(convoyed_order_code, convoyed_order_args, virtual=True)
        convoy_order = self.get_order(Order.CONVOY, (None, convoy_square, convoyed_order), virtual=True)
        order = self.get_order(Order.SUPPORT_CONVOY, (piece, convoy_order), virtual=virtual)
        convoy_order.add_support(order)
        return order
    
    def progress(self):
        for order in self.orders:
            if not order.virtual:
                order.execute(self.board, self.console)
            self.visualizer.erase_order(order)
        self.orders.clear()
    
    def _square(self, square_str):
        """
        Assume that `square_str` is a valid input.
        """
        if len(square_str) < 2:
            return None
        file = ord(square_str[0]) - ord('a')
        rank = int(square_str[1]) - 1
        return Square(file=file, rank=rank)
    
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
                self.get_order(order_code, (piece,))
                return True
            case Order.MOVE:
                landing_square = self._square(args[1])
                self.get_order(order_code, (piece, landing_square))
                return True
            case Order.SUPPORT_HOLD:
                supported_square = self._square(args[1])
                supported_piece = self.board.get_piece(supported_square)
                self.get_support_order(order_code, piece, Order.HOLD, (supported_piece,))
                return True
            case Order.SUPPORT_MOVE:
                supported_square = self._square(args[1])
                supported_piece = self.board.get_piece(supported_square)
                supported_landing_square = self._square(args[3])
                self.get_support_order(order_code, piece, Order.MOVE, (supported_piece, supported_landing_square))
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
                self.get_support_convoy_order(piece, convoy_square, convoyed_order_code, (convoyed_piece, convoy_landing_square))
                return True
            case Order.BUILD:
                piece_chr = args[1].upper() if args[1] else "P"
                piece_code = Piece.piece_dict[piece_chr]
                order = BuildOrder(power, piece_code, starting_square, self.visualizer, self.full_remove_order)
                self.clear_conflicting_orders(order)
                self.add_order(order)
                return True
            case Order.DISBAND:
                order = DisbandOrder(piece, self.visualizer, self.full_remove_order)
                self.clear_conflicting_orders(order)
                self.add_order(order)
                return True
            case _:
                self.console.out("Unknown error!")
                return False
    
    def sandbox(self):
        self.console.out("Beginning sandbox. Awaiting instructions.")
        power = None
        self.visualizer.ion()
        self.visualizer.show()
        stale = True
        while True:
            if stale:
                self.visualizer.render()
            stale = False
            message = self.console.input("> ").lower().replace(' ', '')
            
            if message in ["exit", "quit"]:
                return
            elif message in ["help"]:
                self.console.out("Type \"power\" to specify your power. Type \"build\" to build. Type \"exit\" or \"quit\" to exit.")
            elif message == "orders":
                if not self.orders:
                    self.console.out("No orders to display.")
                else:
                    self.console.out("Current orders:")
                    for order in self.orders:
                        self.console.out(order)
            elif message == "progress":
                self.progress()
                stale = True
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
                order = self.find_order_on_square(square, virtual=False)
                if order is not None:
                    self.retract_order(order)
                    stale = True
            elif power is None:
                self.console.out("No power has been selected. Select a power by writing \"power [name]\"")
            else: # Message is an order
                stale = self._process_order(power, message)


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
    GM.setup_pieces(["K d1", "P c2", "N b1", "Ra1"], "England")
    GM.setup_pieces(["K e1", "P e2", "B f1", "Rh1"], "Italy")
    GM.setup_pieces(["K e8", "P e7", "N g8", "Rh8"], "France")
    GM.setup_pieces(["K d8", "P d7", "B c8", "Ra8"], "Scandinavia")
    
    # GM._process_order(powers[2], "h1sh8h")
    # GM._process_order(powers[2], "f1sh3ch1sh8")
    # GM._process_order(powers[2], "f1sh3ch1h8")
    GM.sandbox()
    
