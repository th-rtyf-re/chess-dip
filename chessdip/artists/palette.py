# -*-coding:utf8-*-

import colorsys
import matplotlib.colors as mc

class PowerPalette:
    """
    Manager for the colors associated to a power. The colors and their uses
    are:
    - black: shadow color for pieces when the power is on the black side of
        the board,
    - dark: color of owned dark squares,
    - neutral: main color of pieces when the power is on the black side of
        the board, and shadow color of pieces when the power is on the
        white side of the board,
    - light: color of owned light squares,
    - white: main color of pieces when the power is on the white side of
        the board.
    """
    def __init__(self, black, dark, neutral, light, white):
        self.black = black
        self.dark = dark
        self.neutral = neutral
        self.light = light
        self.white = white
    
    def generate_colors(self, base_color):
        """
        Generate a palette based on a color. This does not give great
        results.
        
        Parameters:
        ----------
        - base_color. Any acceptable Matplotlib color.
        """
        self.hue = colorsys.rgb_to_hls(*mc.to_rgb(base_color))[0]
        
        black_lightness = .2
        dark_lightness = .4
        neutral_lightness = .6
        light_lightness = .8
        white_lightness = .95
        
        square_saturation = .7
        neutral_saturation = .9
        
        self.black = colorsys.hls_to_rgb(self.hue, black_lightness, neutral_saturation)
        self.light = colorsys.hls_to_rgb(self.hue, light_lightness, square_saturation)
        self.neutral = colorsys.hls_to_rgb(self.hue, neutral_lightness, neutral_saturation)
        self.dark = colorsys.hls_to_rgb(self.hue, dark_lightness, square_saturation)
        self.white = colorsys.hls_to_rgb(self.hue, white_lightness, neutral_saturation)

red_palette = PowerPalette("darkred", "indianred", "firebrick", "lightsalmon", "mistyrose")
green_palette = PowerPalette("darkgreen", "forestgreen", "xkcd:green", "lightgreen", "honeydew")
blue_palette = PowerPalette("midnightblue", "steelblue", "royalblue", "lightskyblue", "aliceblue")
yellow_palette = PowerPalette("saddlebrown", "darkgoldenrod", "goldenrod", "palegoldenrod", "lightyellow")