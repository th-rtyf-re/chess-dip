# -*-coding:utf8-*-

from chessdip.core.order import (
    HoldOrder, MoveOrder, ConvoyOrder, SupportOrder,
    SupportHoldOrder, SupportMoveOrder, SupportConvoyOrder,
    OrderLinker, LinkedOrder,
    BuildOrder, DisbandOrder
)
from chessdip.artists.chess_path import ChessPathArtist, ChessPathArtistManager

class OrderInterface:
    """
    Managing class for orders and their artists.
    """
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.artists = {}
        
    def has_orders(self):
        return bool(self.artists)
    
    def get_orders(self):
        return self.artists.keys()
    
    def get_adjudicable_orders(self):
        orders = []
        for order in self.get_orders():
            if not order.get_virtual() and not isinstance(order, HoldOrder):
                if isinstance(order, LinkedOrder) and order.get_linker() not in orders:
                    orders.append(order.get_linker())
                else:
                    orders.append(order)
        return orders
    
    def clear(self):
        """
        Remove all orders and their artists.
        """
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
        if isinstance(order, LinkedOrder):
            order.get_linker().remove_order(order)
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
        """
        Move the convoys of `other_order` to `order`.
        """
        convoys = other_order.get_convoys()
        order.set_convoys(convoys)
        for convoy_order in convoys:
            convoy_order.set_convoyed_order(order)
            convoy_order.set_virtual(order.get_virtual())
    
    def set_success(self, order, success):
        if isinstance(order, OrderLinker):
            orders = order.get_orders()
        else:
            orders = [order]
        for order in orders:
            self._set_success_single_order(order, success)
        self.visualizer.set_stale()
    
    def _set_success_single_order(self, order, success):
        order.set_success(success)
        self.artists[order].set_success(success)
        supported_order = order.get_supported_order()
        if supported_order is not None:
            self.artists[supported_order].set_support_success(self.artists[order], success)
        for convoy_order in order.get_convoys():
            self.set_success(convoy_order, success)
    
    def recompute_paths(self):
        """
        Experimental; recompute paths using non-overlapping vectors.
        """
        import warnings
        warnings.warn("Recomputing paths is an experimental feature that will probably change in the future.")
        
        CPAM = ChessPathArtistManager(self.visualizer)
        
        items = [(order, artist) for order, artist in self.artists.items() if not isinstance(order, HoldOrder | BuildOrder | DisbandOrder | ConvoyOrder)]
        
        vertices_dict = {}
        
        for order, artist in items:
            CPAM.add_path(artist.path_artist)
        # # Adjust supports
        # for order, artist in items:
        #     if isinstance(order, SupportMoveOrder):
        #         pass
        # Compute most vertices
        for order, artist in items:
            vertices_dict[order] = CPAM.compute_vertices_from_vectors(artist.path_artist)
        # Compute last vertex for supporting artists
        for order, artist in items:
            if isinstance(order, SupportMoveOrder):
                other_vertices = vertices_dict[order.get_supported_order()]
                last_vertices = CPAM.get_intersection(artist.path_artist, other_vertices, default=other_vertices[-2])
                artist.path_artist.junction = last_vertices[-1]
                vertices_dict[order].extend(last_vertices)
            elif isinstance(order, SupportConvoyOrder):
                square = order.get_landing_square()
                supported_order = order.get_supported_order()
                convoyed_order = supported_order.get_convoyed_order()
                convoy_vertex = None
                for vector in self.artists[convoyed_order].path_artist.vectors:
                    if (vector.pos[0], vector.pos[1]) == (square.file, square.rank):
                        convoy_vertex = vector.real_pos
                other_vertices = vertices_dict[convoyed_order]
                last_vertices = CPAM.get_intersection(artist.path_artist, other_vertices, ignore_last=True, default=convoy_vertex)
                artist.path_artist.junction = last_vertices[-1]
                # manually adjust things
                vertices_dict[order] = vertices_dict[order][:-1] + last_vertices
            artist.update_vertices(vertices_dict[order])
            if isinstance(order, SupportOrder):
                self.artists[order.get_supported_order()].update_support_patch(artist)
        self.visualizer.set_stale()