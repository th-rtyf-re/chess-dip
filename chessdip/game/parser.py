# -*-coding:utf8-*-

import re

from chessdip.board.square import Square
from chessdip.board.piece import Piece
from chessdip.core.order import (
    HoldOrder, MoveOrder, ConvoyOrder, SupportOrder,
    SupportHoldOrder, SupportMoveOrder, SupportConvoyOrder,
    OrderLinker, LinkedMoveOrder,
    BuildOrder, DisbandOrder
)

class Parser:
    """
    Class that parses orders via regular expression pattern matching.
    """
    def __init__(self):
        self.piece_dict = {
            'P': Piece.PAWN,
            'N': Piece.KNIGHT,
            'B': Piece.BISHOP,
            'R': Piece.ROOK,
            'K': Piece.KING
        }
        
        piece = "[pnbrk]?"
        square = "[abcdefgh][12345678]"
        supported_action = (
            f"(?P<supported_hold>h?)"
            f"|(?P<supported_move_code>[-xt]?)(?P<supported_landing_square>{square})"
            f"|c(?:{piece})(?P<convoy_starting_square>{square})(?P<convoy_code>[-xts]?)(?P<convoy_landing_square>{square})"
        )
        action = (
            f"(?P<move>-?(?P<landing_square>{square}))"
            f"|(?P<support>s(?:{piece})(?P<supported_starting_square>{square})(?:{supported_action}))"
            f"|(?P<en_passant>(?=(?:|.{{3}})t(?P<ep_travel_square>{square}))(?=(?:|.{{3}})x(?P<ep_attack_square>{square})).{{6}})"
            f"|(?P<hold>h)"
        )
        castle_order = "(?P<long_castle>o-o-o)|(?P<short_castle>o-o)"
        
        self.pattern = (
            f"(?P<normal_order>(?P<piece>{piece})(?P<starting_square>{square})(?:{action}))"
            f"|{castle_order}"
            f"|build(?P<build_piece>{piece})(?P<build_square>{square})"
            f"|disband{piece}(?P<disband_square>{square})"
        )
    
    def parse(self, message):
        m = re.fullmatch(self.pattern, message)
        if m is None:
            return None, tuple()
        elif m["hold"] is not None:
            args = (_square(m["starting_square"]),)
            return HoldOrder, args
        elif m["move"] is not None:
            args = (
                _square(m["starting_square"]),
                _square(m["landing_square"])
            )
            return MoveOrder, args
        elif m["support"] is not None:
            if m["supported_hold"] is not None:
                args = (
                    _square(m["starting_square"]),
                    _square(m["supported_starting_square"])
                )
                return SupportHoldOrder, args
            elif m["supported_landing_square"] is not None:
                args = (
                    _square(m["starting_square"]),
                    _square(m["supported_starting_square"]),
                    m["supported_move_code"],
                    _square(m["supported_landing_square"])
                )
                return SupportMoveOrder, args
            elif m["convoy_starting_square"] is not None:
                args = (
                    _square(m["starting_square"]),
                    _square(m["supported_starting_square"]),
                    _square(m["convoy_starting_square"]), 
                    m["convoy_code"],
                    _square(m["convoy_landing_square"])
                )
                return SupportConvoyOrder, args
        elif m["en_passant"] is not None:
            args = (
                "en_passant",
                _square(m["starting_square"]),
                _square(m["ep_travel_square"]),
                _square(m["ep_attack_square"])
            )
            return OrderLinker, args
        elif m["long_castle"] is not None:
            return OrderLinker, ("long_castle",)
        elif m["short_castle"] is not None:
            return OrderLinker, ("short_castle",)
        elif m["build_piece"] is not None:
            args = (_square(m["build_square"]), m["build_piece"])
            return BuildOrder, args
        elif m["disband_square"] is not None:
            args = (_square(m["disband_square"]),)
            return DisbandOrder, args
        else:
            return None, tuple()
    
    def square(self, square_str):
        """
        Return the Square corresponding to `square_str`, with validation.
        """
        if len(square_str) < 2:
            return None
        if square_str[0] not in "abcdefgh" or square_str[1] not in "12345678":
            raise ValueError(f"Cannot parse square {square_str}")
        return _square(square_str)
    
def _square(square_str):
    """
    Return the Square corresponding to `square_str`. We assume that
    `square_str` is a valid square.
    """
    file = ord(square_str[0]) - ord('a')
    rank = int(square_str[1]) - 1
    return Square(file=file, rank=rank)