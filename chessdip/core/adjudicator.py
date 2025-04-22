# -*-coding:utf8-*-

from enum import Enum

from chessdip.core.order import *

class State(Enum):
    UNRESOLVED = 0
    GUESSING = 1
    RESOLVED = 2

class Adjudicator:
    """
    Shoutouts to Lucas Kruijswijk (https://diplom.org/Zine/S2009M/Kruijswijk/DipMath_Chp6.htm)
    and Talia Parkinson (pydip)
    """
    def __init__(self, order_interface):
        """
        No hold orders, no convoys, no virtual orders!
        """
        self.order_interface = order_interface
        self.orders = [order for order in self.order_interface.get_orders() if not order.get_virtual() and not isinstance(order, HoldOrder | ConvoyOrder)]
        self.resolutions = {order: False for order in self.orders}
        self.states = {order: State.UNRESOLVED for order in self.orders}
        self.dependencies = []
    
    def adjudicate(self):
        for order in self.orders:
            resolution, _ = self._resolve(order)
            self.order_interface.set_success(order, resolution)
    
    def _resolve(self, order):
        if self.states[order] == State.RESOLVED:
            return self.resolutions[order], State.RESOLVED
        elif self.states[order] == State.GUESSING:
            if order not in self.dependencies:
                self.dependencies.append(order)
            return self.resolutions[order], State.GUESSING
        
        # Otherwise, make a guess
        self.resolutions[order] = False
        self.states[order] = State.GUESSING
        old_dep_length = len(self.dependencies)
        fail_guess_resolution, state = self._adjudicate_with_guesses(order)
        
        if state == State.RESOLVED:
            if self.states[order] != State.RESOLVED:
                self.resolutions[order] = fail_guess_resolution
                self.states[order] = State.RESOLVED
            return self.resolutions[order], State.RESOLVED
        elif order not in self.dependencies[old_dep_length:]:
            self.dependencies.append(order)
            self.resolutions[order] = fail_guess_resolution
            return self.resolutions[order], State.GUESSING
        
        # Other guess
        for other_order in self.dependencies[old_dep_length:]:
            self.resolutions[other_order] = State.UNRESOLVED
        self.dependencies = self.dependencies[:old_dep_length]
        self.resolutions[order] = True
        self.states[order] = State.GUESSING
        success_guess_resolution, _ = self._adjudicate_with_guesses(order)
        
        if fail_guess_resolution == success_guess_resolution:
            for other_order in self.dependencies[old_dep_length:]:
                self.resolutions[other_order] = State.UNRESOLVED
            self.resolutions[order] = fail_guess_result
            self.states[order] = State.RESOLVED
            return self.resolutions[order], State.RESOLVED
        
        # Backup rule
        self._backup_rule(self.dependencies[old_dep_length:])
        
        return self._resolve(order)
    
    def _adjudicate_with_guesses(self, order):
        if isinstance(order, MoveOrder):
            return self._adjudicate_move(order)
        elif isinstance(order, SupportOrder):
            return self._adjudicate_support(order)
        else:
            raise ValueError("Adjudicating unexpected type!")
    
    def _adjudicate_move(self, order):
        resolution, state = self._check_convoys(order)
        if state:
            return resolution, state
        return resolution, state
    
    def _adjudicate_support(self, order):
        return True, State.GUESSING
    
    def _check_convoys(self, order):
        """
        Returns:
        -------
        - convoys_ok: bool.
        - state: bool.
        """
        convoys_ok, state = True, State.GUESSING
        for convoy_order in order.get_convoys():
            convoy_strength, _ = self._get_convoy_strength(convoy_order)
            other_orders = self.order_interface.get_other_opposing(convoy_order)
            for other_order in other_orders:
                if isinstance(other_order, HoldOrder):
                    return False, State.RESOLVED
                elif isinstance(other_order, ConvoyOrder):
                    other_convoy_strength, other_state = self._get_convoy_strength(other_order)
                    if other_convoy_strength > convoy_strength and other_state == State.RESOLVED:
                        return False, State.RESOLVED
                    elif other_convoy_strength > convoy_strength:
                        convoys_ok = False
                elif isinstance(other_order, MoveOrder):
                    other_resolution, other_state = self._resolve(other_order)
                    if other_resolution and other_state == State.RESOLVED:
                        return False, State.RESOLVED
                    elif other_resolution:
                        convoys_ok = False
        return convoys_ok, state
    
    def _get_convoy_strength(self, order):
        state = State.RESOLVED
        strength = 0
        for other_order in order.get_supports():
            other_resolution, other_state = self._resolve(other_order)
            if other_resolution:
                strength += 1
            if other_state != State.RESOLVED:
                state = State.GUESSING
        return strength, state
    
    def _backup_rule(self, orders):
        for order in orders:
            if isinstance(order, ConvoyOrder):
                self._apply_szykman(orders)
                return
        self._apply_circular_movement(orders)
    
    def _apply_szykman(self, orders):
        for i in orders:
            if isinstance(order, ConvoyOrder):
                self.resolutions[i] = False
                self.states[order] = State.RESOLVED
            else:
                self.states[order] = State.UNRESOLVED
    
    def _apply_circular_movement(self, orders):
        for i in orders:
            if isinstance(self.orders[order], MoveOrder):
                self.resolutions[order] = True
                self.states[order] = State.RESOLVED
            else:
                self.states[order] = State.UNRESOLVED
    
    def evaluate(self, order):
        if order.get_virtual():
            self.order_manager.set_success(order, False)
            return
        supported_order = order.get_supported_order()
        if supported_order is not None and supported_order.get_virtual():
            self.order_manager.set_success(order, False)
            return
        self.order_manager.set_success(order, True)