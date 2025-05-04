# -*-coding:utf8-*-

from chessdip.board.square import Square
from chessdip.board.power import Side
from chessdip.board.piece import Piece
from chessdip.board.board import Board

class BoardInterface:
    """
    Squares, supply centers, and pieces. Should have the same signature as
    a Board object
    """
    def __init__(self, setup, visualizer):
        self.visualizer = visualizer
        
        self.board = Board(setup)
        self.board_artist = self.visualizer.make_board_artist(self.board)
        self.visualizer.add_artist(self.board_artist)
        
        self.piece_artists = {}
        self.en_passant = []
    
    def clear(self):
        for _, artist in self.piece_artists.items():
            artist.remove()
        self.piece_artists.clear()
        for rank in range(8):
            for file in range(8):
                square = Square(rank=rank, file=file)
                self.set_ownership(square, self.board.get_default_owner(square))
                self.set_sc_ownership(square, self.board.get_default_sc_owner(square))
        self.visualizer.set_stale()
    
    def get_pieces(self):
        return self.piece_artists.keys()
    
    def get_moved(self, piece):
        return piece.moved
    
    def add_piece(self, code, power, square):
        piece = Piece(code, power, square)
        piece.moved = False
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
    
    def update_sc_ownership(self):
        for piece in self.get_pieces():
            square = piece.get_square()
            if square.rank >= 2 and square.rank < 6:
                self.set_sc_ownership(square, piece.get_power())
            elif piece.code == Piece.PAWN:
                if piece.get_power().side == Side.WHITE and square.rank == 7:
                    self.set_sc_ownership(square, piece.get_power())
                elif piece.get_power().side == Side.BLACK and square.rank == 0:
                    self.set_sc_ownership(square, piece.get_power())
        self.visualizer.set_stale()
    
    def vacate_square(self, square):
        for piece in self.get_pieces():
            if piece.get_square() == square:
                self.remove_piece(piece)
                self.visualizer.set_stale()
    
    def move_piece_to(self, piece, square):
        piece.move_to(square)
        piece.moved = True
        self.piece_artists[piece].move_to(square)
        self.set_ownership(square, piece.get_power())
        self.visualizer.set_stale()
    
    def mark_en_passant(self, piece, square):
        self.en_passant.append((piece, square))
    
    def clear_en_passant(self):
        self.en_passant.clear()
    
    def can_en_passant(self, piece, square):
        return (piece, square) in self.en_passant