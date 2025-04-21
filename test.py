# -*-coding:utf8-*-

from chessdip.ui import GameManager
from chessdip.board import Power, Side

if __name__ == "__main__":
    color_dict = {
        "opal": ("honeydew", "limegreen"),
        "quartz": ("mistyrose", "darkred"),
        "obsidian": ("royalblue", "k"),
        "onyx": ("goldenrod", "k"),
        "black": ("k", "k"),
        "white": ("w", "w"),
        "none": ("none", "k")
    }
    powers = [
        Power(0, "neutral", color_dict["none"], ((175/255, 138/255, 105/255), (237/255, 218/255, 185/255)), Side.NEUTRAL),
        Power(1, "England", color_dict["quartz"], ("indianred", "lightsalmon"), Side.WHITE),
        Power(2, "Italy", color_dict["opal"], ("forestgreen", "lightgreen"), Side.WHITE),
        Power(3, "France", color_dict["obsidian"], ("steelblue", "lightskyblue"), Side.BLACK),
        Power(4, "Scandinavia", color_dict["onyx"], ("darkgoldenrod", "palegoldenrod"), Side.BLACK),
        Power(-2, "black", color_dict["black"], ("k", "k"), Side.BLACK),
        Power(-1, "white", color_dict["white"], ("w", "w"), Side.WHITE),
    ]
    GM = GameManager(powers)
    GM.setup_pieces(powers[1], ["K d1", "P c2", "N b1", "Ra1"])
    GM.setup_pieces(powers[2], ["K e1", "P e2", "B f1", "Rh1"])
    # GM.setup_pieces(powers[2], ["K e1", "P e2", "B f1", "Rg1"])
    GM.setup_pieces(powers[3], ["K e8", "P e7", "N g8", "Rh8"])
    GM.setup_pieces(powers[4], ["K d8", "P d7", "B c8", "Ra8"])
    
    # GM.process_orders(powers[2], ["f1sh3ch1sh8", "h1sh8h", "h1sa8h8"])
    # GM.process_orders(powers[2], ["g1sg8ch8f8", "g1sg8ch8sf8", "g1sg8ch8e8"])
    # GM.process_orders(powers[2], ["g1sg8ch8se8", "g1sg8ch8se8"])
    GM.sandbox()