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
    
    GM = GameManager()
    england = GM.add_power("England", color_dict["quartz"], ("indianred", "lightsalmon"), Side.WHITE)
    italy = GM.add_power("Italy", color_dict["opal"], ("forestgreen", "lightgreen"), Side.WHITE)
    france = GM.add_power("France", color_dict["obsidian"], ("steelblue", "lightskyblue"), Side.BLACK)
    scandinavia = GM.add_power("Scandinavia", color_dict["onyx"], ("darkgoldenrod", "palegoldenrod"), Side.BLACK)
    GM.setup_pieces(england, ["K d1", "P c2", "N b1", "Ra1"])
    GM.setup_pieces(italy, ["K e1", "P e2", "B f1", "Rh1"])
    # GM.setup_pieces(italy, ["K e1", "P e2", "B f1", "Rg1"])
    GM.setup_pieces(france, ["K e8", "P e7", "N g8", "Rh8"])
    GM.setup_pieces(scandinavia, ["K d8", "P d7", "B c8", "Ra8"])
    
    # GM.process_orders(powers[2], ["f1sh3ch1sh8", "h1sh8h", "h1sa8h8"])
    # GM.process_orders(powers[2], ["g1sg8ch8f8", "g1sg8ch8sf8", "g1sg8ch8e8"])
    # GM.process_orders(powers[2], ["g1sg8ch8se8", "g1sg8ch8se8"])
    # GM.process_orders(italy, ["h1sh8h", "f1sh3ch1sh8", "f1sh3ch1h8", "h1h8"])
    GM.sandbox()