# -*-coding:utf8-*-

from collections import namedtuple

class Square(namedtuple("Square", ["file", "rank"])):
    """Squares on the chess board."""
    __slots__ = ()
    
    def __str__(self):
        return "abcdefgh"[self.file] + "12345678"[self.rank]