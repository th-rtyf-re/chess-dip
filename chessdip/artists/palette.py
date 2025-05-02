import colorsys
import matplotlib.colors as mc

class PowerPalette:
    def __init__(self, black, dark, neutral, light, white):
        self.black = black
        self.dark = dark
        self.neutral = neutral
        self.light = light
        self.white = white
    
    def generate_colors(self, base_color):
        """
        base_color is a matplotlib color
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
