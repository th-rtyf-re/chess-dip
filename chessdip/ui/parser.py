# -*-coding:utf8-*-

import re

from chessdip.core.order import *

class Parser:
    def __init__(self, order_class):
        self.order_class = order_class
        
        piece = "[pnbrk]?"
        square = "[abcdefgh][12345678]"
        supported_action = (
            f"(?P<supported_hold>h)"
            f"|(?P<supported_move_code>[-xt]?)(?P<supported_landing_square>{square})"
            f"|c(?P<convoy_starting_square>{square})(?P<convoy_code>[-xts]?)(?P<convoy_landing_square>{square})"
        )
        action = (
            f"(?P<move>-?(?P<landing_square>{square}))"
            f"|(?P<support>s(?P<supported_starting_square>{square})(?:{supported_action}))"
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
        elif m["build_piece"] is not None:
            args = (_square(m["build_square"]), m["build_piece"])
            return BuildOrder, args
        elif m["disband_square"] is not None:
            args = (_square(m["disband_square"]),)
            return DisbandOrder, args
        else:
            return None, tuple()
    
def _square(square_str):
    """
    Assume that `square_str` is a valid input.
    """
    if len(square_str) < 2:
        return None
    file = ord(square_str[0]) - ord('a')
    rank = int(square_str[1]) - 1
    return Square(file=file, rank=rank)

def test():
    from order import Order
    
    p = Parser(Order)
    print(p.pattern)
    while True:
        message = input("> ").lower().replace(" ", "")
        if message == "quit":
            return
        else:
            p.parse(message)

if __name__ == "__main__":
    test()