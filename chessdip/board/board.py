# -*-coding:utf8-*-

import numpy as np

from chessdip.board.power import Side

class Board:
    """
    The chess board. This class stores the location of supply centers and
    the ownership of each square and supply center.
    """
    def __init__(self, setup):
        """
        Parameters:
        ----------
        - setup: BoardSetup. Object that encodes the initial state of the
            board.
        """
        self.sc_mask = setup.sc_mask
        self.powers = setup.powers
        self.pieces = []
        self.ownership = np.zeros((8, 8), dtype=int)
        self.sc_ownership = np.zeros((8, 8), dtype=int)
        self.sc_ownership[:2][self.sc_mask[:2]] = Side.WHITE
        self.sc_ownership[-2:][self.sc_mask[-2:]] = Side.BLACK
    
    def set_ownership(self, square, power):
        old_code = self.ownership[square.rank, square.file]
        new_code = self.powers.index(power)
        if old_code != new_code:
            self.ownership[square.rank, square.file] = new_code
            return True
        return False
    
    def set_sc_ownership(self, square, power):
        if not self.sc_mask[square.rank, square.file]:
            return False
        old_code = self.sc_ownership[square.rank, square.file]
        new_code = self.powers.index(power)
        if old_code != new_code:
            self.sc_ownership[square.rank, square.file] = self.powers.index(power)
            return True
        return False
    
    def get_default_owner(self, square):
        return self.powers[Side.NEUTRAL]
    
    def get_default_sc_owner(self, square):
        if square.rank < 2:
            return self.powers[Side.WHITE]
        elif square.rank >= 6:
            return self.powers[Side.BLACK]
        else:
            return self.powers[Side.NEUTRAL]