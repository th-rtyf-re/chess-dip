# -*-coding:utf8-*-

import matplotlib as mpl
from matplotlib.path import Path
import numpy as np

from power import Power
from square import Square
from piece import Piece
from board import Board
from visualizer import Visualizer
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
            Order.CONVOY: None,
            Order.SUPPORT_HOLD: SupportHoldOrder,
            Order.SUPPORT_MOVE: None,
            Order.SUPPORT_CONVOY: None,
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
    
    def make_and_add_order(self, order_code, piece, *args, virtual=False):
        for other_order in self.orders:
            if isinstance(other_order, self.order_subclasses[order_code]) and other_order.is_like(piece, *args):
                order = other_order
                order.set_virtual(order.virtual and virtual)
                return order
        order = self.order_subclasses[order_code](piece, *args, self.visualizer, self.full_remove_order, virtual=virtual)
        self.add_order(order)
        return order
    
    
    def make_and_add_support_order(self, order_code, piece, supported_square, *args, virtual=False):
        supported_order_code = Order.support_order_codes[order_code]
        supported_order = self.find_order_on_square(supported_square, order_code=supported_order_code)
        if supported_order is None:
            supported_order = self.make_order_on_square(supported_order_code, supported_square, *args, virtual=True)
        order = self.make_and_add_order(order_code, piece, supported_order, *args, virtual=False)
        return order
    
    def make_order_on_square(self, order_code, square, *args, **kwargs):
        piece = self.board.get_piece(square)
        if piece is not None:
            order = self.make_and_add_order(order_code, piece, *args, **kwargs)
            return order
        return None
    
    def add_order(self, order):
        for other_order in self.orders:
            if other_order.piece == order.piece and not other_order.virtual and not order.virtual:
                other_order.remove()
                self.orders.append(order)
                self.visualizer.add_order(order)
                return
        self.orders.append(order)
        self.visualizer.add_order(order)
    
    def full_remove_order(self, order):
        self.orders.remove(order)
        self.visualizer.erase_order(order)
    
    def progress(self):
        for order in self.orders:
            if not order.virtual:
                order.execute(self.board, self.console)
            self.visualizer.erase_order(order)
        self.orders.clear()
    
    def _square(self, square_str):
        if len(square_str) < 2:
            return None
        file = ord(square_str[0]) - ord('a')
        rank = int(square_str[1]) - 1
        return Square(file=file, rank=rank)
    
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
            
            # Meta instructions
            if message in ["exit", "quit"]:
                return
            elif message in ["help"]:
                self.console.out("Type \"power\" to specify your power. Type \"build\" to build. Type \"exit\" or \"quit\" to exit.")
                continue
            elif message == "orders":
                if not self.orders:
                    self.console.out("No orders to display.")
                else:
                    self.console.out("Current orders:")
                    for order in self.orders:
                        self.console.out(order)
                continue
            elif message == "progress":
                self.progress()
                stale = True
                continue
            elif message[:len("power")] == "power":
                try:
                    power = self._get_power(message[len("power"):])
                    self.console.out(f"Playing as {power}.")
                except ValueError:
                    self.console.out(f"Power {words[1]} not found.")
                continue
            elif message[:len("remove")] == "remove":
                square = self._square(message[len("remove"):])
                if square is None:
                    continue
                order = self.find_order_on_square(square, virtual=False)
                if order is not None:
                    order.remove()
                    stale = True
                continue
            elif power is None:
                self.console.out("No power has been selected. Select a power by writing \"power [name]\"")
                continue
            
            # Orders
            order_code, args = self.parser.parse(message)
            if order_code is None:
                self.console.out("Could not parse order.")
                continue
            
            starting_square = self._square(args[0])
            piece = self.board.get_piece(starting_square)
            if order_code == Order.BUILD:
                pass
            elif piece is None:
                self.console.out(f"No piece on {starting_square}.")
                continue
            elif piece.power != power:
                self.console.out("Cannot order another power's piece.")
                continue
            
            match order_code:
                case Order.HOLD:
                    self.make_and_add_order(order_code, piece, *args[1:])
                    stale = True
                    continue
                case Order.MOVE:
                    landing_square = self._square(args[1])
                    self.make_and_add_order(order_code, piece, landing_square)
                    stale = True
                    continue
                case Order.SUPPORT_HOLD:
                    supported_square = self._square(args[1])
                    self.make_and_add_support_order(order_code, piece, supported_square)
                    stale = True
                    continue
                case Order.BUILD:
                    piece_chr = args[1].upper() if args[1] else "P"
                    piece_code = Piece.piece_dict[piece_chr]
                    self.add_order(BuildOrder(power, piece_code, starting_square, self.visualizer))
                    stale = True
                    continue
                case Order.DISBAND:
                    self.add_order(DisbandOrder(piece, self.visualizer))
                    stale = True
                    continue
                case None:
                    continue
                case _:
                    self.console.out("Not implemented yet!")
                    continue


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
    
    GM.sandbox()
