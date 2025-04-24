# -*-coding:utf8-*-

from chessdip.core.order import *

class OrderInterface:
    """
    Managing orders and their artists
    """
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.artists = {}
        
    def has_orders(self):
        return bool(self.artists)
    
    def get_orders(self):
        return self.artists.keys()
    
    def clear(self):
        for _, artist in self.artists.items():
            artist.remove()
        self.artists.clear()
        self.visualizer.set_stale()
    
    def add(self, order):
        supported_order = order.get_supported_order()
        supported_artist = None
        if supported_order is not None:
            supported_artist = self.artists[supported_order]
        order_artist = self.visualizer.make_order_artist(order, supported_artist)
        self.artists[order] = order_artist
        self.visualizer.add_artist(order_artist)
        return order
    
    def remove(self, order):
        self.artists[order].remove() # From visualizer
        del self.artists[order]
        self.visualizer.set_stale()
    
    def set_virtual(self, order, virtual=True):
        order.set_virtual(virtual)
        self.artists[order].set_virtual(virtual)
        for convoy_order in order.get_convoys():
            self.set_virtual(convoy_order, virtual)
        self.visualizer.set_stale()
    
    def add_support(self, order, support_order):
        order.add_support(support_order)
        self.artists[order].add_support(self.artists[support_order])
        self.visualizer.set_stale()
    
    def remove_support(self, order, support_order):
        order.remove_support(support_order)
        self.artists[order].remove_support(self.artists[support_order])
        self.visualizer.set_stale()
    
    def add_convoy(self, order, convoy_order):
        order.add_convoy(convoy_order)
    
    def remove_convoy(self, order, convoy_order):
        order.remove_convoy(convoy_order)
    
    def inherit_convoys(self, order, other_order):
        convoys = other_order.get_convoys()
        order.set_convoys(convoys)
        for convoy_order in convoys:
            convoy_order.set_convoyed_order(order)
            convoy_order.set_virtual(order.get_virtual())
    
    def set_success(self, order, success):
        order.set_success(success)
        self.artists[order].set_success(success)
        supported_order = order.get_supported_order()
        if supported_order is not None:
            self.artists[supported_order].set_support_success(self.artists[order], success)
        for convoy_order in order.get_convoys():
            self.set_success(convoy_order, success)
        self.visualizer.set_stale()