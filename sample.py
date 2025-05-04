# -*-coding:utf8-*-

from chessdip.test import test_cases
from chessdip.game import GameManager, standard_setup

def sandbox():
    GM = GameManager(setup=standard_setup)
    GM.setup()
    GM.sandbox()

if __name__ == "__main__":
    # sandbox()
    test_cases(sandbox=False, verbose=False)