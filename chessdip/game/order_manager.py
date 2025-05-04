# -*-coding:utf8-*-

from chessdip.core.order import (
    ConvoyOrder, SupportOrder, SupportConvoyOrder, LinkedOrder
)

from chessdip.interface.order import OrderInterface

class OrderManager(OrderInterface):
    """
    Managing class for an order set. In addition to being an OrderInterface,
    objects of this class can properly add and remove orders so that other
    orders remain valid.
    """
    def __init__(self, visualizer):
        super().__init__(visualizer)
    
    def retract(self, order):
        if isinstance(order, LinkedOrder):
            orders = order.get_linker().get_orders()
        else:
            orders = [order]
        for order in orders:
            self._retract_single_order(order)
        
    def _retract_single_order(self, order):
        # If supported by a real order, keep but make virtual
        for support_order in order.get_supports():
            if not support_order.get_virtual():
                self.set_virtual(order)
                return
        
        # If supporting an order, update the supported order's support list.
        supported_order = order.get_supported_order()
        if supported_order is not None:
            self.remove_support(supported_order, order)
            # If supported order is virtual, try removing that order as well
            if supported_order.get_virtual():
                self.retract(supported_order)
        
        # If convoyed by a supported convoy order, keep in some sense
        for convoy_order in order.get_convoys():
            if convoy_order.get_supports():
                # If order is a support, convert into generic support
                if isinstance(order, SupportOrder):
                    generic_support_order = SupportOrder(order.piece, order.supported_square, virtual=True)
                    self.inherit_convoys(generic_support_order, order)
                    self.remove(order)
                    self.add(generic_support_order)
                else: # Move order: make virtual
                    self.set_virtual(order)
                return
        
        # If convoying an order, try to retract the convoyed order: if that
        # succeeds, then order will also be removed.
        convoyed_order = order.get_convoyed_order()
        if convoyed_order is not None:
            self.retract(convoyed_order)
            return
        
        # Finally, remove order and all convoys
        self.remove(order)
        for convoy_order in order.get_convoys():
            self.remove(convoy_order)
        return
    
    def get_order(self, order_class, args, virtual=False, kwargs=None):
        """
        Find or create the order of class `order_class` using the arguments
        `args` and keyword arguments `kwargs`. In addition to finding the
        exact order, we can also find an inheritable order: an order whose
        properties can be transfered to a new order of a similar type, e.g.
        a SupportOrder that becomes a subclass.
        
        Parameters:
        ----------
        - order_class: a subclass of Order.
        - args: tuple.
        - virtual: bool, optional. Default value is False
        - kwargs: dict or None, optional. If None, then no keyword arguments
            are passed on to the object creation. Default value is None.
        """
        if kwargs is None:
            kwargs = {}
        # find matching order
        inheritable_order = None
        for other_order in self.get_orders():
            if isinstance(other_order, order_class) and args == order_class.get_args(other_order):
                # found matching order.
                order = other_order
                self.set_virtual(order, order.get_virtual() and virtual)
                if not order.get_virtual():
                    self._clear_conflicting_orders(order)
                return order
            elif isinstance(other_order, SupportOrder) and issubclass(order_class, SupportOrder) and other_order.is_inheritable(*args):
                # found inheritable order
                inheritable_order = other_order
                break
        if inheritable_order is not None:
            order = order_class(*args, virtual=virtual, **kwargs)
            self.inherit_convoys(order, inheritable_order)
            if type(inheritable_order) is SupportOrder:
                self.remove(inheritable_order)
            else:
                supported_order = inheritable_order.get_supported_order()
                self.remove_support(supported_order, inheritable_order)
                if supported_order.get_virtual():
                    self.retract(supported_order)
                self.remove(inheritable_order)
                
            self._clear_conflicting_orders(order)
            self.add(order)
            return order
        else:
            # no match: make new order
            order = order_class(*args, virtual=virtual, **kwargs)
            self._clear_conflicting_orders(order)
            self.add(order)
            self.add_convoys(order)
            return order
    
    def _clear_conflicting_orders(self, order):
        if isinstance(order, ConvoyOrder):
            return
        conflicting_orders = []
        for other_order in self.get_orders():
            if isinstance(order, LinkedOrder) and isinstance(other_order, LinkedOrder) and order.get_linker() == other_order.get_linker():
                continue
            elif (other_order is not order
                and other_order.get_piece() == order.get_piece()
                and not other_order.get_virtual()
                and not order.get_virtual()
            ):
                conflicting_orders.append(other_order)
        for other_order in conflicting_orders:
            self.retract(other_order)
    
    def add_convoys(self, order):
        """
        Note that we do not check for conflicting orders.
        """
        for square in order.get_intermediate_squares():
            convoy_order = ConvoyOrder(None, square, order, virtual=order.virtual)
            self.add(convoy_order)
            self.add_convoy(order, convoy_order)
    
    def get_support_order(self, order_class, piece, supported_order_class, supported_order_args, virtual=False):
        supported_order = self.get_order(supported_order_class, supported_order_args, virtual=True)
        order = self.get_order(order_class, (piece, supported_order), virtual=virtual)
        self.add_support(supported_order, order)
        return order
    
    def get_support_convoy_order(self, piece, convoy_square, convoyed_order_class, convoyed_order_args, virtual=False):
        convoyed_order = self.get_order(convoyed_order_class, convoyed_order_args, virtual=True)
        convoy_order = self.get_order(ConvoyOrder, (None, convoy_square, convoyed_order), virtual=True)
        order = self.get_order(SupportConvoyOrder, (piece, convoy_order), virtual=virtual)
        self.add_support(convoy_order, order)
        return order