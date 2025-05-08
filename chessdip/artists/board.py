# -*-coding:utf8-*-

import matplotlib as mpl
import numpy as np

class BoardArtist:
    """
    Artist for the board. This artist colors in squares appropriately.
    """
    def __init__(self, board, global_kwargs):
        self.board = board
        self.ax = None
        
        self.light_mask = np.ones((8, 8), dtype=bool)
        self.light_mask[::2, ::2] = False
        self.light_mask[1::2, 1::2] = False
        
        self.sc_xshift, self.sc_yshift = -.35, -.35
        self.sc_kwargs = dict(radius=.8 * global_kwargs["dot_radius"], ec="k", lw=1.5 * global_kwargs["edge_width"])
        
        self.square_artists = np.full((8, 8), None, dtype=object)
        self.sc_artists = np.full((8, 8), None, dtype=object)
        self.text_patches = [] # for rank and file names, and for phase
    
    def add_to_ax(self, ax, zorder=1.):
        self.ax = ax
        self.ax.set_axis_off()
        self.ax.set_aspect("equal")
        self.ax.set_xlim(-.5, 7.5)
        self.ax.set_ylim(-.5, 7.5)
        
        self.populate_square_artists(self.square_artists, zorder=zorder)
        self.populate_sc_artists(self.sc_artists, zorder=zorder)
        for square_artist in self.square_artists.flat:
            if square_artist is not None:
                self.ax.add_patch(square_artist)
        for sc_artist in self.sc_artists.flat:
            if sc_artist is not None:
                self.ax.add_patch(sc_artist)
        self.add_labels(zorder)
    
    def populate_square_artists(self, square_artists, zorder=1.):
        for rank in range(8):
            for file in range(8):
                patch = self.make_square_patch(rank, file, zorder=zorder)
                square_artists[rank, file] = patch
    
    def populate_sc_artists(self, sc_artists, zorder=1.):
        for rank, file in zip(*self.board.sc_mask.nonzero()):
            power = self.board.powers[self.board.sc_ownership[rank, file]]
            patch = self.make_sc_patch(rank, file, power, zorder=zorder)
            sc_artists[rank, file] = patch
    
    def add_labels(self, zorder=1.):
        for file, file_name in enumerate("abcdefgh"):
            text = self.ax.text(
                file - self.sc_xshift + .07,
                self.sc_yshift - .07,
                file_name,
                c=self.get_opposite_fc(0, file, self.board.powers[0]),
                ha="right",
                va="bottom",
                zorder=zorder
            )
            self.text_patches.append(text)
        for rank, rank_name in enumerate("12345678"):
            text = self.ax.text(
                self.sc_xshift - .07,
                rank - self.sc_yshift + .07,
                rank_name,
                c=self.get_opposite_fc(rank, 0, self.board.powers[0]),
                ha="left",
                va="top",
                zorder=zorder
            )
            self.text_patches.append(text)
        text = self.ax.text(
            7.45,
            7.45,
            "",
            c=self.get_opposite_fc(7, 7, self.board.powers[0]),
            ha="right",
            va="top",
            zorder=zorder
        )
        self.text_patches.append(text)
    
    def make_square_patch(self, rank, file, zorder=1.):
        fc = self.get_square_fc(rank, file, self.board.powers[0])
        patch = mpl.patches.Rectangle((file - .5, rank - .5), 1, 1, fc=fc, ec="none", zorder=zorder)
        return patch
    
    def make_sc_patch(self, rank, file, power, zorder=1.):
        fc = self.get_square_fc(rank, file,  power)
        patch = mpl.patches.Circle((file + self.sc_xshift, rank + self.sc_yshift), fc=fc, **self.sc_kwargs, zorder=zorder)
        return patch
    
    def get_square_fc(self, rank, file, power):
        fc = power.square_color[int(self.light_mask[rank, file])]
        return fc
    
    def get_opposite_fc(self, rank, file, power):
        fc = power.square_color[int(not self.light_mask[rank, file])]
        return fc
    
    def set_owner(self, square, power):
        fc = self.get_square_fc(square.rank, square.file, power)
        self.square_artists[square.rank, square.file].set_fc(fc)
        if square.rank == 0:
            self.text_patches[square.file].set_c(self.get_opposite_fc(square.rank, square.file, power))
        if square.file == 0:
            self.text_patches[square.rank + 8].set_c(self.get_opposite_fc(square.rank, square.file, power))
        if square.rank == 7 and square.file == 7:
            self.text_patches[-1].set_c(self.get_opposite_fc(square.rank, square.file, power))
    
    def set_sc_owner(self, square, power):
        fc = self.get_square_fc(square.rank, square.file, power)
        self.sc_artists[square.rank, square.file].set_fc(fc)
    
    def set_phase(self, phase_str):
        self.text_patches[-1].set_text(phase_str)