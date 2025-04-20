# -*-coding:utf8-*-

# from chessdip.core.order import *

class Adjudicator:
    def __init__(self, order_manager):
        self.order_manager = order_manager
    
    def adjudicate(self):
        for order in self.order_manager.get_orders():
            self.evaluate(order)
    
    def evaluate(self, order):
        if order.get_virtual():
            self.order_manager.set_success(order, False)
            return
        supported_order = order.get_supported_order()
        if supported_order is not None and supported_order.get_virtual():
            self.order_manager.set_success(order, False)
            return
        self.order_manager.set_success(order, True)