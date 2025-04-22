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
    and Talia Parkinson (pydip).
    
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
            if self.states[order] != State.RESOLVED:
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
            self.results[order] = fail_guess_result
            self.states[order] = State.RESOLVED
            return self.results[order], True
        
        # Backup rule
        self._backup_rule(self.dependencies[old_dep_length:])
        
        return self._resolve(order)
    
    # def _resolve(self, order):
    #     if self.states[order] == State.RESOLVED:
    #         return self.results[order], State.RESOLVED
    #     elif self.states[order] == State.GUESSING:
    #         if order not in self.dependencies:
    #             self.dependencies.append(order)
    #         return self.results[order], State.GUESSING
        
    #     # Otherwise, make a guess
    #     self.results[order] = False
    #     self.states[order] = State.GUESSING
    #     old_dep_length = len(self.dependencies)
    #     fail_guess_result, state = self._adjudicate_with_guesses(order)
        
    #     if state == State.RESOLVED:
    #         if self.states[order] != State.RESOLVED:
    #             self.results[order] = fail_guess_result
    #             self.states[order] = State.RESOLVED
    #         return self.results[order], State.RESOLVED
    #     elif order not in self.dependencies[old_dep_length:]:
    #         self.dependencies.append(order)
    #         self.results[order] = fail_guess_result
    #         return self.results[order], State.GUESSING
        
    #     # Other guess
    #     for other_order in self.dependencies[old_dep_length:]:
    #         self.results[other_order] = State.UNRESOLVED
    #     self.dependencies = self.dependencies[:old_dep_length]
    #     self.results[order] = True
    #     self.states[order] = State.GUESSING
    #     success_guess_result, _ = self._adjudicate_with_guesses(order)
        
    #     if fail_guess_result == success_guess_result:
    #         for other_order in self.dependencies[old_dep_length:]:
    #             self.results[other_order] = State.UNRESOLVED
    #         self.results[order] = fail_guess_result
    #         self.states[order] = State.RESOLVED
    #         return self.results[order], State.RESOLVED
        
    #     # Backup rule
    #     self._backup_rule(self.dependencies[old_dep_length:])
        
    #     return self._resolve(order)
    
    def _adjudicate_with_guesses(self, order):
        if isinstance(order, MoveOrder):
            return self._adjudicate_move(order)
        elif isinstance(order, SupportOrder):
            return self._adjudicate_support(order)
        else:
            raise ValueError("Adjudicating unexpected type!")
    
    def _adjudicate_move(self, order):
        opposing_orders = self.order_interface.get_other_opposing(order)
        order_at_landing = self._get_order_at_landing(order)
        min_attack, max_attack = self._get_attack_strength(order, order_at_landing)
        
        result, certain = True, True
        if isinstance(order_at_landing, MoveOrder) and order_at_landing.get_landing_square() == order.get_starting_square():
            # Head-to-head
            min_defend, max_defend = self._get_defend_strength(order_at_landing)
            if min_defend > max_attack:
                return False, True
            elif max_defend > max_attack:
                result, certain = False, False
            elif min_attack > max_defend:
                pass
            elif max_attack > max_defend:
                certain = False
        else:
            min_hold, max_hold = self._get_hold_strength(order.get_landing_square())
            if min_hold > max_attack:
                return False, True
            elif max_hold > max_attack:
                result, certain = False, False
            elif min_attack > max_hold:
                pass
            elif max_attack > max_hold:
                certain = False
            
        for other_order in opposing_orders:
            min_prevent, max_prevent = self._get_prevent_strength(other_order, order_at_landing)
            if min_prevent > max_attack: # certain failure
                return False, True
            elif max_prevent > max_attack: # guessed failure
                result, certain = False, False
            elif min_attack > max_prevent: # certain success
                pass
            elif max_attack > max_prevent: # guessed success
                certain = False
        return result, certain
    
    def _get_hold_strength(self, square):
        order = self._get_order_for_hold_strength(square)
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
            min_hold, max_hold = 1, 1
            for support_order in self._get_real_supports(order):
                support_result, support_certain = self._resolve(support_order)
                if support_result:
                    max_hold += 1
                    if support_certain:
                        min_hold += 1
            return min_hold, max_hold
            
            
    
    def _get_order_for_hold_strength(self, square):
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
    
    def _get_prevent_strength(self, order, order_at_landing):
        result, certain = self._resolve(order)
        if not result:
            return 0, 0
        
        if isinstance(order, ConvoyOrder):
            min_prevent, max_prevent = 0, 0
            for support_order in self._get_real_supports(order):
                support_result, support_certain = self._resolve(support_order)
                if support_result:
                    max_prevent += 1
                    if support_certain:
                        min_prevent += 1
            return min_prevent, max_prevent
        else:
            if (order_at_landing is not None
                and isinstance(order_at_landing, MoveOrder)
                and order_at_landing.get_landing_square() == order.get_starting_square()
            ): # head-to-head
                result_at_landing, certain_at_landing = self._resolve(order_at_landing)
                if result_at_landing: # head-to-head success
                    return 0, 0
                elif not certain_at_landing: # guessed head-to-head failure
                    max_prevent = 1
                    for support_order in self._get_real_supports(order):
                        support_result, _ = self._resolve(support_order)
                        if support_result:
                            max_prevent += 1
                    return 0, max_prevent
            else: # certain head-to-head failure or no head-to-head
                min_prevent, max_prevent = 1, 1
                for support_order in self._get_real_supports(order):
                    support_result, support_certain = self._resolve(support_order)
                    if support_result:
                        max_prevent += 1
                        if support_certain:
                            min_prevent += 1
                return min_prevent, max_prevent
            
        
    
    def _get_defend_strength(self, order):
        min_defend, max_defend = 1, 1
        for support_order in self._get_real_supports(order):
            support_result, support_certain = self._resolve(support_order)
            if support_result:
                max_defend += 1
                if support_certain:
                    min_defend += 1
        return min_defend, max_defend
        
    def _get_attack_strength(self, order, order_at_landing):
        result, _ = self._check_path(order)
        if not result:
            return 0, 0
        
        if order_at_landing is None:
            min_attack, max_attack = 1, 1
            for support_order in self._get_real_supports(order):
                support_result, support_certain = self._resolve(support_order)
                if support_result:
                    max_attack += 1
                    if support_certain:
                        min_attack += 1
            return min_attack, max_attack
        elif isinstance(order_at_landing, MoveOrder) and order_at_landing.get_landing_square() != order.get_starting_square():
            # no head-to-head
            result_at_landing, certain_at_landing = self._resolve(order_at_landing)
            if result_at_landing and certain_at_landing: # certain success
                min_attack, max_attack = 1, 1
                for support_order in self._get_real_supports(order):
                    support_result, support_certain = self._resolve(support_order)
                    if support_result:
                        max_attack += 1
                        if support_certain:
                            min_attack += 1
                return min_attack, max_attack
            elif result_at_landing: # guessed success
                max_attack = 1
                for support_order in self._get_real_supports(order):
                    support_result, _ = self._resolve(support_order)
                    if support_result:
                        max_attack += 1
                return 0, max_attack
            else: # failure
                return 0, 0
        elif order_at_landing.get_piece().get_power() == order.get_piece().get_power():
            return 0, 0
        else:
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
                
        
    
    def _check_path(self, order):
        result, certain = True, True
        for convoy_order in order.get_convoys():
            order_at_landing = self._get_order_for_hold_strength(convoy_order.get_landing_square())
            if isinstance(order_at_landing, MoveOrder):
                result_at_landing, certain_at_landing = self._resolve(order_at_landing)
                if not result_at_landing and certain_at_landing:
                    return False, True
                else:
                    result = result and result_at_landing
                    certain = certain and certain_at_landing
            elif isinstance(order_at_landing, HoldOrder):
                return False, True
            
            min_convoy, max_convoy = self._get_convoy_strength(convoy_order)
            other_orders = self.order_interface.get_other_opposing(convoy_order)
            for other_order in other_orders:
                if isinstance(other_order, HoldOrder):
                    return False, True
                elif isinstance(other_order, ConvoyOrder):
                    other_min_convoy, other_max_convoy = self._get_convoy_strength(other_order)
                    if other_min_convoy > max_convoy: # certain failure
                        return False, True
                    elif other_max_convoy > max_convoy: # guessed failure
                        result, certain = False, False
                    elif min_convoy > other_max_convoy: # certain success
                        pass
                    elif max_convoy > other_max_convoy: # guessed success
                        certain = False
                elif isinstance(other_order, MoveOrder):
                    other_result, other_certain = self._resolve(other_order)
                    if other_result and other_certain:
                        return False, True
                    else:
                        result = result and (not other_result)
                        certain = certain and other_certain
        return result, certain
    
    def _get_convoy_strength(self, order):
        min_convoy, max_convoy = 0, 0
        for support_order in self._get_real_supports(order):
            support_result, support_certain = self._resolve(support_order)
            if support_result:
                max_convoy += 1
            if support_result and support_certain:
                min_convoy += 1
        return min_convoy, max_convoy
    
    # def _adjudicate_move(self, order):
        
    #     opposing_orders = self.order_interface.get_other_opposing(order)
    #     order_at_landing = self._get_order_at_landing(order)
    #     attack_strength, attack_state = self._get_attack_strength(order, order_at_landing)
    #     success_vs_prevent, state_vs_prevent = self._get_success_vs_prevent(attack_strength, opposing_orders)
        
    #     if isinstance(order_at_landing, MoveOrder) and order_at_landing.get_landing_square() == order.get_starting_square():
    #         # Head-to-head
    #         success_vs_landing, state_vs_landing = self._get_success_vs_defend(attack_strength, order_at_landing)
    #     else:
    #         success_vs_landing, state_vs_landing = self._get_success_vs_hold(attack_strength)
    #     result = success_path and success_vs_prevent and state_vs_landing
    #     if state_path == State.GUESSING or state_vs_prevent == State.GUESSING or state_vs_landing == State.GUESSING:
    #         return result, State.GUESSING
    #     else:
    #         return result, State.RESOLVED
    
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
    
    # def _get_head_to_head(self, order):
    #     for other_order in self.orders:
    #         if (isinstance(other_order, MoveOrder)
    #             and order.get_landing_square() == other_order.get_starting_square()
    #             and other_order.get_landing_square() == order.get_starting_square()
    #         ):
    #             return other_order
    #     return None
    
    # def _get_success_vs_prevent(self, attack_strength, other_orders):
    #     success = True
    #     state = State.RESOLVED
    #     for other_order in other_orders:
    #         prevent_strength, other_state = self._get_prevent_strength(order)
    #         if prevent_strength > attack_strength:
    #             if other_state == State.RESOLVED:
    #                 return False, State.RESOLVED
    #             else:
    #                 success = False
    #         if other_state == State.GUESSING:
    #             state = State.GUESSING
    #     return success, state
        
    
    def _adjudicate_support(self, order):
        return True, False
    
    # def _check_path(self, order):
    #     """
    #     Returns:
    #     -------
    #     - convoys_ok: bool.
    #     - state: State.
    #     """
    #     path_success = True
    #     for convoy_order in order.get_convoys():
    #         convoy_strength, _ = self._get_convoy_strength(convoy_order)
    #         other_orders = self.order_interface.get_other_opposing(convoy_order)
    #         for other_order in other_orders:
    #             if isinstance(other_order, HoldOrder):
    #                 return False, State.RESOLVED
    #             elif isinstance(other_order, ConvoyOrder):
    #                 other_convoy_strength, other_state = self._get_convoy_strength(other_order)
    #                 if other_convoy_strength > convoy_strength and other_state == State.RESOLVED:
    #                     return False, State.RESOLVED
    #                 elif other_convoy_strength > convoy_strength:
    #                     path_success = False
    #             elif isinstance(other_order, MoveOrder):
    #                 other_result, other_state = self._resolve(other_order)
    #                 if other_result and other_state == State.RESOLVED:
    #                     return False, State.RESOLVED
    #                 elif other_result:
    #                     path_success = False
    #     return path_success, State.GUESSING
    
    # def _get_convoy_strength(self, order):
    #     state = State.RESOLVED
    #     strength = 0
    #     for other_order in self._get_real_supports(order):
    #         other_result, other_state = self._resolve(other_order)
    #         if other_result:
    #             strength += 1
    #         if other_state != State.RESOLVED:
    #             state = State.GUESSING
    #     return strength, state
    
    # def _get_attack_strength(self, order, order_at_landing):
    #     success, state = self._check_path(order)
    #     if not success and state == State.RESOLVED:
    #         return 0, State.RESOLVED
        
    #     if order_at_landing is None:
    #         if not success:
    #             return 0, State.GUESSING
    #         else:
    #             strength = 1
    #             for support_order in self._get_real_supports(order):
    #                 support_success, support_state = self._resolve(support_order)
    #                 if support_success:
    #                     strength += 1
    #                 if support_state != State.RESOLVED:
    #                     state = State.GUESSING
    #     head_to_head = 
    #     success_at_landing, state_at_landing = self._resolve(order_at_landing)
    #     if 
        
    #     state = State.RESOLVED
    #     strength = 0
    #     for other_order in self._get_real_supports(order):
    #         other_result, other_state = self._resolve(other_order)
    #         if other_result:
    #             strength += 1
    #         if other_state != State.RESOLVED:
    #             state = State.GUESSING
    #     return strength, state
    
    def _backup_rule(self, orders):
        for order in orders:
            if isinstance(order, ConvoyOrder):
                self._apply_szykman(orders)
                return
        self._apply_circular_movement(orders)
    
    def _apply_szykman(self, orders):
        for i in orders:
            if isinstance(order, ConvoyOrder):
                self.results[i] = False
                self.states[order] = State.RESOLVED
            else:
                self.states[order] = State.UNRESOLVED
    
    def _apply_circular_movement(self, orders):
        for i in orders:
            if isinstance(self.orders[order], MoveOrder):
                self.results[order] = True
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