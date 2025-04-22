# -*-coding:utf8-*-

from chessdip.board.piece import Piece
from chessdip.board.board import Board

class BoardInterface:
    """
    Squares, supply centers, and pieces. Should have the same signature as
    a Board object
    """
    def __init__(self, powers, visualizer):
        self.visualizer = visualizer
        
        self.board = Board(powers)
        self.board_artist = self.visualizer.make_board_artist(self.board)
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