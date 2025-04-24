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
    and Talia Parkinson (pydip) and DATC (https://webdiplomacy.net/doc/DATC_v3_0.html#5.F).
    
    Here, we are basically keeping track of two results: certain successes and
    guessed results. For strengths this means a minimal strength and a guessed
    strength.
    """
    def __init__(self, order_interface):
        """
        No hold orders, no convoys, no virtual orders!
        """
        self.order_interface = order_interface
        self.orders = [order for order in self.order_interface.get_orders() if not order.get_virtual() and not isinstance(order, HoldOrder | ConvoyOrder)]
        self.results = {order: False for order in self.orders}
        self.states = {order: State.UNRESOLVED for order in self.orders}
        self.dependencies = []
    
    def adjudicate(self):
        for order in self.orders:
            result, _ = self._resolve(order)
            self.order_interface.set_success(order, result)
        # Set virtual moves to fail
        for order in self.order_interface.get_orders():
            if order.get_virtual():
                self.order_interface.set_success(order, False)
    
    def _resolve(self, order):
        if self.states[order] == State.RESOLVED:
            return self.results[order], True
        elif self.states[order] == State.GUESSING:
            if order not in self.dependencies:
                self.dependencies.append(order)
            return self.results[order], False
        
        # Otherwise, make a guess
        self.results[order] = False
        self.states[order] = State.GUESSING
        old_dep_length = len(self.dependencies)
        fail_guess_result, certain = self._adjudicate_with_guesses(order)
        
        if certain:
            self.results[order] = fail_guess_result
            self.states[order] = State.RESOLVED
            return self.results[order], True
        elif order not in self.dependencies[old_dep_length:]:
            self.dependencies.append(order)
            self.results[order] = fail_guess_result
            return self.results[order], False
        
        # Other guess
        for other_order in self.dependencies[old_dep_length:]:
            self.results[other_order] = State.UNRESOLVED
        self.dependencies = self.dependencies[:old_dep_length]
        self.results[order] = True
        self.states[order] = State.GUESSING
        success_guess_result, _ = self._adjudicate_with_guesses(order)
        
        if fail_guess_result == success_guess_result:
            for other_order in self.dependencies[old_dep_length:]:
                self.results[other_order] = State.UNRESOLVED
            self.dependencies = self.dependencies[:old_dep_length]
            self.results[order] = fail_guess_result
            self.states[order] = State.RESOLVED
            return self.results[order], True
        
        # Backup rule
        self._backup_rule(self.dependencies[old_dep_length:])
        self.dependencies = self.dependencies[:old_dep_length]
        return self._resolve(order)
    
    # Main adjudication functions
    
    def _adjudicate_with_guesses(self, order):
        if isinstance(order, MoveOrder):
            return self._adjudicate_move(order)
        elif isinstance(order, SupportOrder):
            return self._adjudicate_support(order)
        else:
            raise ValueError(f"Adjudicating unexpected order: {order}")
    
    def _backup_rule(self, orders):
        for order in orders:
            if isinstance(order, ConvoyOrder):
                self._apply_szykman(orders)
                return
        self._apply_circular_movement(orders)
    
    def _apply_szykman(self, orders):
        for order in orders:
            if isinstance(order, ConvoyOrder):
                self.results[order] = False
                self.states[order] = State.RESOLVED
            else:
                self.states[order] = State.UNRESOLVED
    
    def _apply_circular_movement(self, orders):
        for order in orders:
            if isinstance(self.orders[order], MoveOrder):
                self.results[order] = True
                self.states[order] = State.RESOLVED
            else:
                self.states[order] = State.UNRESOLVED
    
    # Core adjudication functions
    
    def _adjudicate_move(self, order):
        order_at_landing = self._get_order_at_landing(order)
        attack_strength = self._get_attack_strength(order, order_at_landing)
        
        result_guess = _certain_true
        if isinstance(order_at_landing, MoveOrder) and order_at_landing.get_landing_square() == order.get_starting_square():
            # Head-to-head
            defend_strength = self._get_defend_strength(order_at_landing)
            result_guess = _guess_and(_guess_lt(defend_strength, attack_strength), result_guess)
            if _certain_not(result_guess):
                return _certain_false
        else: # No head-to-head
            hold_strength = self._get_hold_strength(order.get_landing_square())
            result_guess = _guess_and(_guess_lt(hold_strength, attack_strength), result_guess)
            if _certain_not(result_guess):
                return _certain_false
        
        # Get prevent strengths
        opposing_orders = self._get_other_opposing(order)
        for other_order in opposing_orders:
            prevent_strength = self._get_prevent_strength(other_order, order_at_landing)
            result_guess = _guess_and(_guess_lt(prevent_strength, attack_strength), result_guess)
            if _certain_not(result_guess):
                return _certain_false
        return result_guess
    
    def _adjudicate_support(self, order):
        result_guess = self._check_path(order)
        if _certain_not(result_guess):
            return _certain_false
        
        for other_order in self.orders:
            if (isinstance(other_order, MoveOrder)
                and other_order.get_landing_square() == order.get_starting_square()
            ): # checking for dislodges
                dislodge_success = self._resolve(other_order)
                result_guess = _guess_and(_guess_not(dislodge_success), result_guess)
                if _certain_not(result_guess):
                    return _certain_false
                
                if (other_order.get_piece().get_power() != order.get_piece().get_power()
                    and order.get_landing_square() != other_order.get_starting_square()
                ): # checking for cut support
                    cut_success = self._check_path(other_order)
                    result_guess = _guess_and(_guess_not(cut_success), result_guess)
                    if _certain_not(result_guess):
                        return _certain_false
        return result_guess
    
    def _check_path(self, order):
        if not order.chess_path.valid:
            return _certain_false
        result_guess = _certain_true
        for convoy_order in order.get_convoys():
            order_at_landing = self._get_move_or_hold(convoy_order.get_landing_square())
            if isinstance(order_at_landing, MoveOrder):
                move_success = self._resolve(order_at_landing)
                result_guess = _guess_and(move_success, result_guess)
                if _certain_not(result_guess):
                    return _certain_false
            elif isinstance(order_at_landing, HoldOrder):
                return _certain_false
            
            convoy_strength = self._get_convoy_strength(convoy_order)
            other_orders = self._get_other_opposing(convoy_order)
            for other_order in other_orders:
                if isinstance(other_order, HoldOrder):
                    return _certain_false
                elif isinstance(other_order, ConvoyOrder):
                    other_convoy_strength = self._get_convoy_strength(other_order)
                    result_guess = _guess_and(_guess_lt(other_convoy_strength, convoy_strength), result_guess)
                    if _certain_not(result_guess):
                        return _certain_false
                elif isinstance(other_order, MoveOrder):
                    other_success = self._resolve(other_order)
                    result_guess = _guess_and(_guess_not(other_success), result_guess)
                    if _certain_not(result_guess):
                        return _certain_false
        return result_guess

    # Strength computations
    
    def _get_hold_strength(self, square):
        order = self._get_move_or_hold(square)
        if order is None:
            return 0, 0
        elif isinstance(order, MoveOrder):
            result, certain = self._resolve(order)
            if result: # move success
                return 0, 0
            elif certain: # certain move failure
                return 1, 1
            else: # guessed move failure
                return 0, 1
        else: # count support-holds
            min_support, max_support = self._get_support_strength(order)
            return min_support + 1, max_support + 1
    
    def _get_prevent_strength(self, order, order_at_landing):
        if isinstance(order, ConvoyOrder):
            result, certain = self._resolve(order.get_convoyed_order())
            if not result: # convoy failed
                return 0, 0
            elif certain: # certain convoy success
                min_support, max_support = self._get_support_strength(order)
                return min_support, max_support
            else: # guessed convoy success
                max_support = self._get_guessed_support_strength(order)
                return 0, max_support
        
        result, certain = self._check_path(order)
        if not result:
            return 0, 0
        else:
            if (order_at_landing is not None
                and isinstance(order_at_landing, MoveOrder)
                and order_at_landing.get_landing_square() == order.get_starting_square()
            ): # head-to-head
                success_at_landing = self._resolve(order_at_landing)
                result, certain = _guess_and(success_at_landing, (result, certain))
                if result: # head-to-head success
                    return 0, 0
                elif not certain: # guessed head-to-head failure
                    max_support = self._get_guessed_support_strength(order)
                    return 0, max_support + 1
            else: # certain head-to-head failure or no head-to-head
                min_support, max_support = self._get_support_strength(order)
                return min_support + 1, max_support + 1
    
    def _get_defend_strength(self, order):
        min_support, max_support = self._get_support_strength(order)
        return min_support + 1, max_support + 1
        
    def _get_attack_strength(self, order, order_at_landing):
        result, certain = self._check_path(order)
        if not result:
            return 0, 0
        
        if order_at_landing is None:
            min_support, max_support = self._get_support_strength(order)
            return min_support + 1, max_support + 1
        elif (isinstance(order_at_landing, MoveOrder)
            and order_at_landing.get_landing_square() != order.get_starting_square()
        ): # no head-to-head, piece is attempting to vacate square
            success_at_landing = self._resolve(order_at_landing)
            result, certain = _guess_and(success_at_landing, (result, certain))
            if result and certain: # certain vacate success
                min_support, max_support = self._get_support_strength(order)
                return min_support + 1, max_support + 1
            elif result: # guessed vacate success
                max_support = self._get_guessed_support_strength(order)
                return 0, max_support + 1
            else: # vacate failure
                return 0, 0
        elif order_at_landing.get_piece().get_power() == order.get_piece().get_power():
            return 0, 0
        else: # head-to-head
            min_attack, max_attack = 1, 1
            power_at_landing = order_at_landing.get_piece().get_power()
            for support_order in self._get_real_supports(order):
                if support_order.get_piece().get_power() != power_at_landing:
                    support_result, support_certain = self._resolve(support_order)
                    if support_result:
                        max_attack += 1
                        if support_certain:
                            min_attack += 1
            return min_attack, max_attack
    
    def _get_convoy_strength(self, order):
        min_convoy, max_convoy = self._get_support_strength(order)
        return min_convoy, max_convoy
    
    def _get_support_strength(self, order):
        min_support, max_support = 0, 0
        for support_order in self._get_real_supports(order):
            support_result, support_certain = self._resolve(support_order)
            if support_result:
                max_support += 1
                if support_certain:
                    min_support += 1
        return min_support, max_support
    
    def _get_guessed_support_strength(self, order):
        support = 0
        for support_order in self._get_real_supports(order):
            support_result, _ = self._resolve(support_order)
            if support_result:
                support += 1
        return support
    
    # Order retrieval
    
    def _get_other_opposing(self, order):
        """
        Get other orders with the same landing square.
        """
        ret = []
        for other_order in self.order_interface.get_orders():
            if (other_order is not order
                and other_order.get_landing_square() == order.get_landing_square()
                and not other_order.get_virtual()
                and isinstance(other_order, MoveOrder | ConvoyOrder)
            ):
                ret.append(other_order)
        return ret
    
    def _get_move_or_hold(self, square):
        """
        If there is a move order, return that. Otherwise, if there is a hold
        order, return that. Otherwise, return None.
        """
        for order in self.orders:
            if isinstance(order, MoveOrder) and order.get_starting_square() == square:
                return order
        for order in self.order_interface.get_orders():
            if isinstance(order, HoldOrder) and order.get_starting_square() == square:
                return order
        return None
    
    def _get_order_at_landing(self, order):
        """
        no convoys
        """
        for other_order in self.orders:
            if other_order.get_starting_square() == order.get_landing_square() and not isinstance(other_order, ConvoyOrder):
                return other_order
        return None
    
    def _get_real_supports(self, order):
        return [support_order for support_order in order.get_supports() if not support_order.get_virtual()]
    
# Guessing logic

_certain_true = True, True
_certain_false = False, True

def _certain_not(p):
    return (not p[0]) and p[1]

def _guess_not(p):
    return not p[0], p[1]

def _guess_and(p, q):
    if _certain_not(p) or _certain_not(q):
        return _certain_false
    else:
        return p[0] and p[1], q[0] and q[1]

def _guess_lt(a, b):
    if a[1] < b[0]:
        return _certain_true
    elif a[0] >= b[1]:
        return _certain_false
    else:
        return a[1] < b[1], False