# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from chessdip.board.square import Square
from chessdip.board.power import Power, Side
from chessdip.board.piece import Piece
from chessdip.core.order import *
from chessdip.core.adjudicator import Adjudicator
from chessdip.ui.parser import Parser

from chessdip.interface.board import BoardInterface
from chessdip.interface.order import OrderInterface
from chessdip.interface.visual import VisualInterface

class Console:
    def __init__(self):
        pass
    
    def out(self, *args, **kwargs):
        print(*args, **kwargs)
    
    def input(self, *args, **kwargs):
        return input(*args, **kwargs)
    
class OrderManager(OrderInterface):
    def __init__(self, visualizer):
        super().__init__(visualizer)
    
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
                    self.set_virtual(order)
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
    
    def get_order(self, order_class, args, virtual=False):
        """
        args is what is used to construct the order.
        """
        # order_subclass = self.order_subclasses[order_code]
        # find matching order
        inheritable_order = None
        for other_order in self.get_orders():
            if isinstance(other_order, order_class) and args == order_class.get_args(other_order):
                # found matching order.
                order = other_order
                self.set_virtual(order, order.get_virtual() and virtual)
                if not order.get_virtual():
                    self._clear_conflicting_orders(order)
                return order
            elif isinstance(other_order, SupportOrder) and issubclass(order_class, SupportOrder) and other_order.is_inheritable(*args):
                # found inheritable order
                inheritable_order = other_order
                break
        if inheritable_order is not None:
            order = order_class(*args, virtual=virtual)
            self.inherit_convoys(order, inheritable_order)
            if type(inheritable_order) is SupportOrder:
                self.remove(inheritable_order)
            else:
                supported_order = inheritable_order.get_supported_order()
                self.remove_support(supported_order, inheritable_order)
                if supported_order.get_virtual():
                    self.retract(supported_order)
                self.remove(inheritable_order)
                
            self._clear_conflicting_orders(order)
            self.add(order)
            return order
        else:
            # no match: make new order
            order = order_class(*args, virtual=virtual)
            self._clear_conflicting_orders(order)
            self.add(order)
            self.add_convoys(order)
            return order
    
    def _clear_conflicting_orders(self, order):
        if isinstance(order, ConvoyOrder):
            return
        conflicting_orders = []
        for other_order in self.get_orders():
            if other_order is not order and other_order.get_piece() == order.get_piece() and not other_order.get_virtual() and not order.get_virtual():
                conflicting_orders.append(other_order)
        for other_order in conflicting_orders:
            self.retract(other_order)
    
    def add_convoys(self, order):
        """
        This is the only place where convoys are added. Note that we do not
        check for conflicting orders.
        """
        for square in order.get_intermediate_squares():
            convoy_order = ConvoyOrder(None, square, order, virtual=order.virtual)
            self.add(convoy_order)
            self.add_convoy(order, convoy_order)
    
    def get_support_order(self, order_class, piece, supported_order_code, supported_order_args, virtual=False):
        supported_order = self.get_order(supported_order_code, supported_order_args, virtual=True)
        order = self.get_order(order_class, (piece, supported_order), virtual=virtual)
        self.add_support(supported_order, order)
        return order
    
    def get_support_convoy_order(self, piece, convoy_square, convoyed_order_class, convoyed_order_args, virtual=False):
        convoyed_order = self.get_order(convoyed_order_class, convoyed_order_args, virtual=True)
        convoy_order = self.get_order(ConvoyOrder, (None, convoy_square, convoyed_order), virtual=True)
        order = self.get_order(SupportConvoyOrder, (piece, convoy_order), virtual=virtual)
        self.add_support(convoy_order, order)
        return order

class GameManager:
    def __init__(self):
        self.powers = [
            Power(0, "neutral", ("none", "k"), ((175/255, 138/255, 105/255), (237/255, 218/255, 185/255)), Side.NEUTRAL),
            Power(-2, "black", ("k", "k"), ("k", "k"), Side.BLACK),
            Power(-1, "white", ("w", "w"), ("w", "w"), Side.WHITE),
        ]
        
        self._next_power_code = 1
        self.visualizer = VisualInterface()
        self.order_manager = OrderManager(self.visualizer)
        self.console = Console()
        self.board = BoardInterface(self.powers, self.visualizer)
        self.parser = Parser(Order)
        
        self.piece_dict = {
            'P': Piece.PAWN,
            'N': Piece.KNIGHT,
            'B': Piece.BISHOP,
            'R': Piece.ROOK,
            'K': Piece.KING
        }
    
    def add_power(self, *args, **kwargs):
        power = Power(self._next_power_code, *args, **kwargs)
        self.powers.append(power)
        self._next_power_code += 1
        return power
    
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
        if not power_name:
            raise ValueError(f"Could not find power {power_name}!")
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
    
    def adjudicate(self):
        self._add_holds()
        adjudicator = Adjudicator(self.order_manager)
        adjudicator.adjudicate()
        self._make_disbands()
    
    def _add_holds(self):
        """
        Add or make real the hold orders for non-moving pieces.
        """
        has_order = {piece: 0 for piece in self.board.get_pieces()}# 1 for move order, 2 for hold order, 0 for other
        for order in self.order_manager.get_orders():
            if isinstance(order, MoveOrder) and not order.get_virtual():
                has_order[order.get_piece()] = 1
            elif isinstance(order, HoldOrder):
                self.order_manager.set_virtual(order, False)
        for piece, v in has_order.items():
            if v == 0:
                self.order_manager.add(HoldOrder(piece))
    
    def _make_disbands(self):
        disband_orders = []
        for order in self.order_manager.get_orders():
            if isinstance(order, MoveOrder) and order.get_success():
                piece = self.board.get_piece(order.get_landing_square())
                if piece is not None:
                    disband_orders.append(DisbandOrder(piece))
        for order in disband_orders:
            self.order_manager.add(order)
    
    def progress(self):
        for order in self.order_manager.get_orders():
            if not order.get_virtual():
                order.execute(self.board, self.console)
        self.order_manager.clear()
    
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
        order_class, args = self.parser.parse(message)
        if order_class is None:
            self.console.out("Could not parse order.")
            return False
        
        starting_square = self._square(args[0])
        piece = self.board.get_piece(starting_square)
        if order_class is BuildOrder:
            pass
        elif piece is None:
            self.console.out(f"No piece on {starting_square}.")
            return False
        elif piece.power != power:
            self.console.out("Cannot order another power's piece.")
            return False
        
        if order_class is HoldOrder:
            self.order_manager.get_order(order_class, (piece,))
            return True
        elif order_class is MoveOrder:
            landing_square = self._square(args[1])
            self.order_manager.get_order(order_class, (piece, landing_square))
            return True
        elif order_class is SupportHoldOrder:
            supported_square = self._square(args[1])
            supported_piece = self.board.get_piece(supported_square)
            if supported_piece is None:
                self.console.out(f"No piece on {supported_square} to support.")
                return False
            self.order_manager.get_support_order(order_class, piece, HoldOrder, (supported_piece,))
            return True
        elif order_class is SupportMoveOrder:
            supported_square = self._square(args[1])
            supported_piece = self.board.get_piece(supported_square)
            supported_landing_square = self._square(args[3])
            if supported_piece is None:
                self.console.out(f"No piece on {supported_square} to support.")
                return False
            self.order_manager.get_support_order(order_class, piece, MoveOrder, (supported_piece, supported_landing_square))
            return True
        elif order_class is SupportConvoyOrder:
            convoy_square = self._square(args[1])
            convoy_starting_square = self._square(args[2])
            convoyed_piece = self.board.get_piece(convoy_starting_square)
            if convoyed_piece is None:
                self.console.out(f"No piece on {convoy_starting_square} to support convoy.")
                return False
            convoyed_order_class = SupportOrder if args[3] == 's' else MoveOrder
            convoy_landing_square = self._square(args[4])
            _, intermediate_squares = ChessPath.validate_path(convoyed_piece, convoy_starting_square, convoy_landing_square)
            if convoy_square not in intermediate_squares:
                self.console.out("Convoying square cannot convoy along specified path.")
                return False
            self.order_manager.get_support_convoy_order(piece, convoy_square, convoyed_order_class, (convoyed_piece, convoy_landing_square))
            return True
        elif order_class is BuildOrder:
            piece_chr = args[1].upper() if args[1] else "P"
            piece_code = self.piece_dict[piece_chr]
            order = BuildOrder(power, piece_code, starting_square)
            self.order_manager._clear_conflicting_orders(order)
            self.order_manager.add(order)
            return True
        elif order_class is DisbandOrder:
            order = DisbandOrder(piece)
            self.order_manager._clear_conflicting_orders(order)
            self.order_manager.add(order)
            return True
        else:
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
            elif message == "adjudicate"[:len(message)]:
                self.adjudicate()
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
        Power(0, "neutral", color_dict["none"], ((175/255, 138/255, 105/255), (237/255, 218/255, 185/255)), Side.NEUTRAL),
        Power(1, "England", color_dict["quartz"], ("indianred", "lightsalmon"), Side.WHITE),
        Power(2, "Italy", color_dict["opal"], ("forestgreen", "lightgreen"), Side.WHITE),
        Power(3, "France", color_dict["obsidian"], ("steelblue", "lightskyblue"), Side.BLACK),
        Power(4, "Scandinavia", color_dict["onyx"], ("darkgoldenrod", "palegoldenrod"), Side.BLACK),
        Power(-2, "black", color_dict["black"], ("k", "k"), Side.BLACK),
        Power(-1, "white", color_dict["white"], ("w", "w"), Side.WHITE),
    ]
    GM = GameManager(powers)
    GM.setup_pieces(powers[1], ["K d1", "P c2", "N b1", "Ra1"])
    GM.setup_pieces(powers[2], ["K e1", "P e2", "B f1", "Rh1"])
    # GM.setup_pieces(powers[2], ["K e1", "P e2", "B f1", "Rg1"])
    GM.setup_pieces(powers[3], ["K e8", "P e7", "N g8", "Rh8"])
    GM.setup_pieces(powers[4], ["K d8", "P d7", "B c8", "Ra8"])
    
    # GM.process_orders(powers[2], ["f1sh3ch1sh8", "h1sh8h", "h1sa8h8"])
    # GM.process_orders(powers[2], ["g1sg8ch8f8", "g1sg8ch8sf8", "g1sg8ch8e8"])
    # GM.process_orders(powers[2], ["g1sg8ch8se8", "g1sg8ch8se8"])
    GM.sandbox()
    
