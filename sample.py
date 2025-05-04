# -*-coding:utf8-*-

from chessdip.test import test_cases
from chessdip.ui import GameManager

def sandbox():
    GM = GameManager()
    GM.setup(variant="chess-dip")
    GM.sandbox()

if __name__ == "__main__":
    sandbox()
    # test_cases(sandbox=False, verbose=False)