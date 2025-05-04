# -*-coding:utf8-*-

from chessdip.board.piece import Piece
from chessdip.board.chess_path import ChessPath
from chessdip.core.order import (
    HoldOrder, MoveOrder, ConvoyOrder, SupportOrder,
    SupportHoldOrder, SupportMoveOrder, SupportConvoyOrder,
    OrderLinker, LinkedMoveOrder,
    BuildOrder, DisbandOrder
)
from chessdip.core.adjudicator import Adjudicator

from chessdip.interface.board import BoardInterface
from chessdip.interface.visual import VisualInterface

from chessdip.game.parser import Parser
from chessdip.game.board_setup import BoardSetup
from chessdip.game.phase import Phase
from chessdip.game.order_manager import OrderManager

class Console:
    """
    Class for user input and output.
    """
    def __init__(self):
        pass
    
    def out(self, *args, **kwargs):
        print(*args, **kwargs)
    
    def input(self, *args, **kwargs):
        return input(*args, **kwargs)

class GameManager:
    """
    Managing class for a game.
    """
    def __init__(self, board=None):
        if board is None:
            self.board_setup = BoardSetup()
        else:
            self.board_setup = board
        
        self.visualizer = VisualInterface()
        self.order_manager = OrderManager(self.visualizer)
        self.console = Console()
        self.board = BoardInterface(self.board_setup, self.visualizer)
        self.parser = Parser()
        
        self.powers = self.board_setup.get_true_powers()
        
        self.adjudicator_verbose = False
        
        self.year = 1
        self.phase = Phase.SPRING
    
    def clear_board(self):
        self.board.clear()
        self.order_manager.clear()
    
    def get_powers(self):
        return self.powers
    
    def update_view(self):
        self.visualizer.render()
    
    def setup(self):
        for power, instructions in self.board_setup.pieces:
            self.setup_pieces(power, instructions)
    
    def setup_pieces(self, power, instructions):
        for instruc in instructions:
            instruc = instruc.replace(" ", "")
            piece_code = self.parser.piece_dict[instruc[0]]
            square = self.parser.square(instruc[1:3])
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
    
    def set_adjudicator_verbose(self, verbose):
        self.adjudicator_verbose = verbose
    
    def adjudicate(self):
        self._add_holds()
        adjudicator = Adjudicator(self.order_manager, verbose=self.adjudicator_verbose)
        adjudicator.adjudicate()
        self._make_disbands()
    
    def _add_holds(self):
        """
        Add or make real the hold orders for non-moving pieces.
        """
        has_move_order = {piece: False for piece in self.board.get_pieces()}
        for order in self.order_manager.get_orders():
            if isinstance(order, MoveOrder) and not order.get_virtual() and order.chess_path.valid:
                has_move_order[order.get_piece()] = True
        for order in self.order_manager.get_orders():
            if isinstance(order, HoldOrder) and not has_move_order[order.get_piece()]:
                self.order_manager.set_virtual(order, False)
        for piece, b in has_move_order.items():
            if not b:
                self.order_manager.add(HoldOrder(piece))
    
    def _make_disbands(self):
        failed_move = {piece: False for piece in self.board.get_pieces()}
        for order in self.order_manager.get_orders():
            if isinstance(order, MoveOrder) and not order.get_success():
                failed_move[order.get_piece()] = True
            elif isinstance(order, HoldOrder):
                failed_move[order.get_piece()] = True
        disband_orders = []
        for order in self.order_manager.get_orders():
            if isinstance(order, MoveOrder) and order.get_success():
                piece = self.board.get_piece(order.get_landing_square())
                if piece is not None and failed_move[piece]:
                    disband_orders.append(DisbandOrder(piece))
        for order in disband_orders:
            self.order_manager.add(order)
    
    def progress(self):
        self.board.clear_en_passant()
        for order in self.order_manager.get_orders():
            if not order.get_virtual():
                order.execute(self.board, self.console)
        self.order_manager.clear()
        if self.phase == Phase.FALL:
            self.update_sc_ownership()
        elif self.phase == Phase.WINTER:
            self.year += 1
        self.phase = Phase((self.phase + 1) % Phase.N_PHASES)
    
    def update_sc_ownership(self):
        self.board.update_sc_ownership()
    
    def process_orders(self, power, messages):
        for message in messages:
            self._process_order(power, message.lower().replace(' ', ''))
    
    def add_en_passant(self, power, starting_square, travel_square, attack_square):
        pawn_piece = self.board.get_piece(starting_square)
        if pawn_piece is None or pawn_piece.code != Piece.PAWN:
            self.console.out(f"No pawn on {starting_square}.")
            return False
        passed_pawn_piece = self.board.get_piece(attack_square)
        if passed_pawn_piece is None or passed_pawn_piece.code != Piece.PAWN:
            self.console.out(f"No pawn on {attack_square} to attack.")
        elif not self.board.can_en_passant(passed_pawn_piece, travel_square):
            self.console.out(f"{passed_pawn_piece} is not open to en passant.")
        else:
            linker = OrderLinker()
            self.order_manager.get_order(LinkedMoveOrder, (linker, pawn_piece, travel_square), kwargs=dict(move_type=MoveOrder.TRAVEL))
            self.order_manager.get_order(LinkedMoveOrder, (linker, pawn_piece, attack_square), kwargs=dict(move_type=MoveOrder.ATTACK, exception="en_passant"))
    
    def add_castle(self, power, long=False):
        king_square = power.get_king_square()
        if long:
            rook_square = power.get_queen_rook_square()
        else:
            rook_square = power.get_king_rook_square()
        king_piece = self.board.get_piece(king_square)
        rook_piece = self.board.get_piece(rook_square)
        if king_piece is None:
            self.console.out(f"No king on {king_square} to castle.")
            return False
        elif rook_piece is None:
            self.console.out(f"No rook on {rook_square} to castle.")
            return False
        elif self.board.get_moved(king_piece):
            self.console.out(f"{king_piece} already moved.")
            return False
        elif self.board.get_moved(rook_piece):
            self.console.out(f"{rook_piece} already moved.")
            return False
        elif long: # queenside castle
            linker = OrderLinker()
            self.order_manager.get_order(LinkedMoveOrder, (linker, king_piece, power.get_queenside_castle_king_square()), kwargs=dict(move_type=MoveOrder.TRAVEL, exception="castle"))
            self.order_manager.get_order(LinkedMoveOrder, (linker, rook_piece, power.get_queenside_castle_rook_square()), kwargs=dict(move_type=MoveOrder.TRAVEL, exception="castle"))
            return True
        else: # kingside castle
            linker = OrderLinker()
            self.order_manager.get_order(LinkedMoveOrder, (linker, king_piece, power.get_kingside_castle_king_square()), kwargs=dict(move_type=MoveOrder.TRAVEL, exception="castle"))
            self.order_manager.get_order(LinkedMoveOrder, (linker, rook_piece, power.get_kingside_castle_rook_square()), kwargs=dict(move_type=MoveOrder.TRAVEL, exception="castle"))
            return True
    
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
        
        if order_class is OrderLinker: # special linked orders
            if args[0] == "en_passant":
                return self.add_en_passant(power, *args[1:])
            elif args[0] == "long_castle":
                return self.add_castle(power, long=True)
            elif args[0] == "short_castle":
                return self.add_castle(power, long=False)
            return False
        
        starting_square = args[0]
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
            landing_square = args[1]
            kwargs = None
            if piece.code == Piece.PAWN and starting_square.file == landing_square.file:
                kwargs = dict(move_type=MoveOrder.TRAVEL)
            elif piece.code == Piece.PAWN:
                kwargs = dict(move_type=MoveOrder.ATTACK)
            self.order_manager.get_order(order_class, (piece, landing_square), kwargs=kwargs)
            return True
        elif order_class is SupportHoldOrder:
            supported_square = args[1]
            supported_piece = self.board.get_piece(supported_square)
            if supported_piece is None:
                self.console.out(f"No piece on {supported_square} to support.")
                return False
            self.order_manager.get_support_order(order_class, piece, HoldOrder, (supported_piece,))
            return True
        elif order_class is SupportMoveOrder:
            supported_square = args[1]
            supported_piece = self.board.get_piece(supported_square)
            supported_landing_square = args[3]
            if supported_piece is None:
                self.console.out(f"No piece on {supported_square} to support.")
                return False
            self.order_manager.get_support_order(order_class, piece, MoveOrder, (supported_piece, supported_landing_square))
            return True
        elif order_class is SupportConvoyOrder:
            convoy_square = args[1]
            convoy_starting_square = args[2]
            convoyed_piece = self.board.get_piece(convoy_starting_square)
            if convoyed_piece is None:
                self.console.out(f"No piece on {convoy_starting_square} to support convoy.")
                return False
            convoyed_order_class = SupportOrder if args[3] == 's' else MoveOrder
            convoy_landing_square = args[4]
            _, intermediate_squares = ChessPath.validate_path(convoyed_piece, convoy_landing_square)
            if convoy_square not in intermediate_squares:
                self.console.out("Convoying square cannot convoy along specified path.")
                return False
            self.order_manager.get_support_convoy_order(piece, convoy_square, convoyed_order_class, (convoyed_piece, convoy_landing_square))
            return True
        elif order_class is BuildOrder:
            piece_chr = args[1].upper() if args[1] else "P"
            piece_code = self.parser.piece_dict[piece_chr]
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
                self.console.out("Exiting sandbox.")
                return
            elif message in ["help"]:
                self.console.out(
"""
==== ENTERING ORDERS ====
Before entering an order, make sure that you have specified your power
by entering "power <name>". Consult the `RULES.md` file for how to write
orders. Example: as Italy, you may order Kd1 e1.

==== OTHER COMMANDS ====
All commands are case insensitive:
 - adjudicate, or any distinct prefix (e.g. "adj"): adjudicate the
   current order set.
 - clear: clear the board.
 - exit: exit the sandbox. Alias: quit.
 - help: print this message.
 - orders: print the current order set.
 - power <name>: specify the current power. <name> can be a distinct
   prefix, e.g. "ita" for "Italy".
 - progress: progress the board by moving pieces.
 - quit: exit the sandbox. Alias: exit.
 - redraw (EXPERIMENTAL): redraw paths so that there is less overlap.
   This is an experimental feature.
 - remove <square>: remove the order on the given square.
 - save <filename>: save the current board via Matplotlib's `savefig`
   function. Default extension is `.png`.
"""[1:-1] # remove first and last newlines
                )
            elif message == "adjudicate"[:len(message)]:
                self.adjudicate()
            elif message == "clear":
                self.clear_board()
            elif message == "orders":
                if not self.order_manager.has_orders():
                    self.console.out("No orders to display.")
                else:
                    self.console.out("Current orders:")
                    for order in self.order_manager.get_orders():
                        self.console.out(order)
            elif message[:len("power")] == "power":
                power_str = message[len("power"):]
                try:
                    power = self._get_power(power_str)
                    self.console.out(f"Playing as {power}.")
                except ValueError:
                    self.console.out(f"Power {power_str} not found.")
            elif message[:len("progress")] == "progress":
                self.progress()
                phase = ["winter", "spring", "fall"][self.phase]
                self.console.out(f"Moving on to the {phase} phase.")
            elif message == "redraw"[:len(message)]:
                self.order_manager.recompute_paths()
            elif message[:len("remove")] == "remove":
                square = self.parser.square(message[len("remove"):])
                if square is None:
                    continue
                order = self._find_order_on_square(square, virtual=False)
                if order is None:
                    continue
                elif order.get_piece().get_power() != power:
                    self.console.out(f"Cannot remove another power's order.")
                else:
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