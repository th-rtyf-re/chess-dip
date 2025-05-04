# -*-coding:utf8-*-

import numpy as np

from chessdip.board.power import Power, Side
from chessdip.artists.palette import PowerPalette, red_palette, green_palette, blue_palette, yellow_palette

class GameSetup:
    def __init__(self, powers=None, sc_mask=None, pieces=None):
        self.powers = [
            Power("neutral", PowerPalette("k", (175/255, 138/255, 105/255), "none", (237/255, 218/255, 185/255), "none"), Side.NEUTRAL),
            Power("white", PowerPalette("w", "w", "w", "w", "w"), Side.WHITE),
            Power("black", PowerPalette("k", "k", "k", "k", "k"), Side.BLACK),
        ]
        if powers is not None:
            self.powers.extend(powers)
        
        if sc_mask is None:
            self.sc_mask = np.zeros((8, 8), dtype=bool)
        else:
            self.sc_mask = sc_mask
        
        if pieces is None:
            self.pieces = []
        else:
            self.pieces = pieces
    
    def set_powers(self, powers):
        self.powers.extend(powers)
    
    def set_sc_mask(self, sc_mask):
        self.sc_mask = sc_mask
    
    def set_pieces(self, pieces):
        self.pieces = pieces
    
    def get_true_powers(self):
        return self.powers[3:]
    
standard_setup = GameSetup()
england = Power("England", red_palette, Side.WHITE, d_king=True)
italy = Power("Italy", green_palette, Side.WHITE)
france = Power("France", blue_palette, Side.BLACK)
scandinavia = Power("Scandinavia", yellow_palette, Side.BLACK, d_king=True)
standard_setup.set_powers([england, italy, france, scandinavia])
standard_setup.set_sc_mask(np.array([
    [1, 1, 0, 1, 1, 1, 0, 1],
    [0, 0, 1, 0, 1, 0, 0, 1],
    [0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 0],
    [1, 1, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 0, 1],
    [0, 1, 0, 1, 1, 0, 0, 0],
    [1, 0, 1, 1, 1, 0, 1, 1]
], dtype=bool))
standard_setup.set_pieces([
    (england, ["K d1", "P c2", "N b1"]),
    (italy, ["K e1", "P e2", "B f1"]),
    (france, ["K e8", "P e7", "N g8"]),
    (scandinavia, ["K d8", "P d7", "B c8"])
])