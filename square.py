# -*-coding:utf8-*-

from collections import namedtuple

class Square(namedtuple("Square", ["file", "rank"])):
    __slots__ = ()
    
    def __str__(self):
        return "abcdefgh"[self.file] + "12345678"[self.rank]