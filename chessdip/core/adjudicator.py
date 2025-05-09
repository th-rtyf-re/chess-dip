# -*-coding:utf8-*-

from enum import Enum

from chessdip.core.order import (
    HoldOrder, MoveOrder, ConvoyOrder, SupportOrder, OrderLinker, LinkedOrder
)

class State(Enum):
    UNRESOLVED = 0
    GUESSING = 1
    RESOLVED = 2

class Adjudicator:
    """
    Class implementing the partial information algorithm of the Diplomacy
    Adjudicator Test Cases (DATC) v3.0 by Lucas B. Kruijswijk, Section 5.E:
        https://webdiplomacy.net/doc/DATC_v3_0.html#5.E
    
    Other sources of inspiration were:
    - The Math of Adjudication by Lucas B. Kruijwijk:
        https://diplom.org/Zine/S2009M/Kruijswijk/DipMath_Chp6.htm
    - the `pydip` package by Talia Parkinson:
        https://github.com/taparkins/pydip/
    
    If `verbose` is True, then the adjudicator reports each call to the
    `_resolve` and `_adjudicate` functions, and reports the output.
    """
    def __init__(self, order_interface, verbose=False):
        self.order_interface = order_interface
        self.orders = self.order_interface.get_adjudicable_orders()
        self.result = {order: False for order in self.orders}
        self.resolved = {order: False for order in self.orders}
        self.visited = {order: False for order in self.orders}
        self.cycle = []
        self.recursion_hits = 0
        self.uncertain = True
        
        self.verbose = verbose
        self._debug_call_depth = 0
    
    # ==== Main adjudication functions ====
    
    def adjudicate(self):
        """
        Adjudicate the current order set. This function assumes that hold
        orders were properly added: that is, every piece that does not have
        a move order, has a hold order, even if that piece was not ordered
        to hold.
        """
        for order in self.orders:
            result = self._resolve(order, True)
            self.order_interface.set_success(order, result)
        # Set virtual moves to fail
        for order in self.order_interface.get_orders():
            if order.get_virtual():
                self.order_interface.set_success(order, False)
    
    def _resolve(self, order, optimistic):
        """
        Implementation of the final partial information algorithm as described
        in Section 5.E of the DATC v3.0.
        
        There is one modification: checking that `recursion_hits` is equal
        to `old_recursion_hits` only happens if the order is in `cycle`. I
        think that this is needed to address orders belonging to multiple
        cycles, but I have not checked it. The algorithm seems to work,
        according to the DATC tests.
        """
        self._debug_out(f"Resolve {order} {self._debug_optimistic(optimistic)}")
        self._debug_call_depth += 1
        
        if isinstance(order, LinkedOrder):
            order = order.get_linker()
        
        if self.resolved[order]:
            self._debug_out_decr(f"1. end resolve: {self._debug_result(self.result[order])}, {self._debug_resolved(order)}")
            return self.result[order]
        elif order in self.cycle:
            self.uncertain = True
            self._debug_out_decr(f"2. end resolve: in cycle, uncertain, {self._debug_result(optimistic)}, {self._debug_resolved(order)}")
            return optimistic
        elif self.visited[order]:
            self.cycle.append(order)
            self.recursion_hits += 1
            self.uncertain = True
            self._debug_out_decr(f"3. end resolve: visited, uncertain, {self._debug_result(optimistic)}, {self._debug_resolved(order)}")
            return optimistic
        
        self.visited[order] = True
        old_cycle_len = len(self.cycle)
        old_recursion_hits = self.recursion_hits
        old_uncertain = self.uncertain
        
        self.uncertain = False
        opt_result = self._adjudicate(order, True)
        if self.uncertain and opt_result:
            pes_result = self._adjudicate(order, False)
        else:
            pes_result = opt_result
        self.visited[order] = False
        
        if opt_result == pes_result:
            self.cycle = self.cycle[:old_cycle_len]
            self.recursion_hits = old_recursion_hits
            self.uncertain = old_uncertain
            self.result[order] = opt_result
            self.resolved[order] = True
            self._debug_out_decr(f"4. end resolve: {self._debug_result(opt_result)}, {self._debug_resolved(order)}")
            return opt_result
        
        elif order in self.cycle:
            self.recursion_hits -= 1
            
            # I think that this should only happen if order is in cycle?
            if self.recursion_hits == old_recursion_hits:
                self._backup_rule(self.cycle[old_cycle_len:])
                self.cycle = self.cycle[:old_cycle_len]
                self.uncertain = old_uncertain
                ret = self._resolve(order, optimistic)
                self._debug_out_decr(f"5. end resolve: ancestor of cycle, {self._debug_result(ret)}, {self._debug_resolved(order)}")
                return ret
        
        elif not order in self.cycle:
            self.cycle.append(order)
        self._debug_out_decr(f"6. end resolve: not ancestor of cycle, {self._debug_result(optimistic)}, {self._debug_resolved(order)}")
        return optimistic
    
    def _adjudicate(self, order, optimistic):
        self._debug_out(f"Adjudicate {order} {self._debug_optimistic(optimistic)}")
        self._debug_call_depth += 1
        if isinstance(order, OrderLinker):
            ret = self._adjudicate_linker(order, optimistic)
        elif isinstance(order, MoveOrder):
            ret = self._adjudicate_move(order, optimistic)
        elif isinstance(order, SupportOrder):
            ret = self._adjudicate_support(order, optimistic)
        elif isinstance(order, ConvoyOrder):
            ret = self._adjudicate_convoy(order, optimistic)
        else:
            raise ValueError(f"Adjudicating unexpected order: {order}")
        self._debug_out_decr(f"end adjudicate: {self._debug_result(ret)}")
        return ret
    
    def _backup_rule(self, orders):
        self._debug_out(f"backup rule")
        if not orders:
            raise NameError("No orders in backup!")
        for order in orders:
            self._debug_out(f"with: {order}")
        for order in orders:
            if isinstance(order, ConvoyOrder):
                self._apply_szykman(orders)
                return
        self._apply_circular_movement(orders)
    
    def _apply_szykman(self, orders):
        self._debug_out(f"applying Szykman's rule")
        for order in orders:
            if isinstance(order, ConvoyOrder):
                self._debug_out(f"failing {order}")
                self.result[order] = False
                self.resolved[order] = True
            else:
                self.resolved[order] = False
    
    def _apply_circular_movement(self, orders):
        self._debug_out(f"applying circular movement")
        for order in orders:
            if isinstance(order, MoveOrder):
                self._debug_out(f"circulating {order}")
                self.result[order] = True
                self.resolved[order] = True
            else:
                self.resolved[order] = False
    
    # ==== Core adjudication functions ====
    
    def _adjudicate_linker(self, linker, optimistic):
        for order in linker.get_orders():
            if not self._adjudicate(order, optimistic):
                return False
        return True
    
    def _adjudicate_move(self, order, optimistic):
        order_at_landing = self._get_order_at_landing(order)
        attack_strength = self._get_attack_strength(order, order_at_landing, optimistic)
        # self._debug_out(f"got attack strength {attack_strength} for {order}")
        
        if (isinstance(order_at_landing, MoveOrder)
            and order_at_landing.get_landing_square() == order.get_starting_square()
            and order_at_landing.chess_path.valid
        ): # Head-to-head
            defend_strength = self._get_defend_strength(order_at_landing, not optimistic)
            if defend_strength >= attack_strength:
                return False
        else: # No head-to-head
            hold_strength = self._get_hold_strength(order.get_landing_square(), not optimistic)
            # self._debug_out(f"got hold strength {hold_strength}")
            if hold_strength >= attack_strength:
                return False
        
        # Get prevent strengths
        opposing_orders = self._get_other_opposing(order)
        for other_order in opposing_orders:
            prevent_strength = self._get_prevent_strength(other_order, order_at_landing, not optimistic)
            # self._debug_out(f"got prevent strength {prevent_strength} for {other_order}")
            if prevent_strength >= attack_strength:
                return False
        return True
    
    def _adjudicate_support(self, order, optimistic):
        if not self._check_path(order, optimistic):
            return False
        
        supported_order = order.get_supported_order()
        if isinstance(supported_order, ConvoyOrder) and not self._check_path(supported_order, optimistic):
            return False
        for other_order in self.orders:
            if (isinstance(other_order, MoveOrder)
                and other_order.get_landing_square() == order.get_starting_square()
            ): # checking for dislodge
                if self._resolve(other_order, not optimistic):
                    return False
                if (other_order.get_piece().get_power() != order.get_piece().get_power()
                    and order.get_landing_square() != other_order.get_starting_square()
                    and order.get_landing_square() not in other_order.get_intermediate_squares()
                    and self._check_path(other_order, not optimistic)
                ): # checking for cut
                    return False
        return True
    
    def _adjudicate_convoy(self, order, optimistic):
        if not self._check_path(order, optimistic):
            return False
        
        order_at_landing = self._get_move(order.get_landing_square())
        if order_at_landing is not None:
            # check if piece moves away
            if not self._resolve(order_at_landing, optimistic):
                return False
        else:
            order_at_landing = self._get_hold(order.get_landing_square())
            if order_at_landing is not None:
                # a piece is holding; convoy cannot succeed
                return False
        
        convoy_strength = self._get_prevent_strength(order, None, optimistic)
        other_orders = self._get_other_opposing(order)
        for other_order in other_orders:
            if isinstance(other_order, ConvoyOrder): # competing convoy
                other_convoy_strength = self._get_prevent_strength(other_order, None, not optimistic)
                if other_convoy_strength >= convoy_strength:
                    return False
            elif isinstance(other_order, MoveOrder): # attacking piece
                if self._resolve(other_order, not optimistic):
                    return False
        return True
    
    def _check_path(self, order, optimistic):
        if isinstance(order, ConvoyOrder): # check earlier convoys
            for other_order in order.get_convoyed_order().get_convoys():
                if other_order is order:
                    return True
                elif not self._resolve(other_order, optimistic):
                    return False
        
        if not order.chess_path.valid:
            return False
        
        for convoy_order in order.get_convoys():
            if not self._resolve(convoy_order, optimistic):
                return False
        return True
    
    # ==== Strength computations ====
    
    def _get_hold_strength(self, square, optimistic):
        # self._debug_out(f"Getting hold strength at {square}")
        order = self._get_move(square)
        if order is not None and order.chess_path.valid:
            if self._resolve(order, not optimistic): # we want the move to fail
                return 0
            else:
                return 1
        else: # count support-holds of hold order
            order = self._get_hold(square)
            if order is not None:
                return 1 + self._get_support_strength(order, optimistic)
        return 0
    
    def _get_prevent_strength(self, order, order_at_landing, optimistic):
        # self._debug_out(f"Getting prevent strength of {order}")
        if not self._check_path(order, optimistic):
            return 0
        elif isinstance(order, ConvoyOrder):
            return max(0.5, self._get_support_strength(order, optimistic))
        elif (order_at_landing is not None
            and isinstance(order_at_landing, MoveOrder)
            and order_at_landing.get_landing_square() == order.get_starting_square()
            and self._resolve(order_at_landing, not optimistic)
        ): # head-to-head succeeds
            return 0
        else: # head-to-head fails or no head-to-head
            return (0 if order.is_travel() else 1) + self._get_support_strength(order, optimistic)
    
    def _get_defend_strength(self, order, optimistic):
        if not order.chess_path.valid:
            return 0
        else:
            return (0 if order.is_travel() else 1)  + self._get_support_strength(order, optimistic)
        
    def _get_attack_strength(self, order, order_at_landing, optimistic):
        # self._debug_out(f"Getting attack strength of {order}")
        if not self._check_path(order, optimistic):
            return 0
        
        if order_at_landing is None:
            return max(0.5, (0 if order.is_travel() else 1) + self._get_support_strength(order, optimistic))
        elif (isinstance(order_at_landing, MoveOrder)
            and order_at_landing.get_landing_square() != order.get_starting_square()
            and self._resolve(order_at_landing, optimistic)
        ): # no head-to-head, piece at landing moves
            return max(0.5, (0 if order.is_travel() else 1) + self._get_support_strength(order, optimistic))
        elif order_at_landing.get_piece().get_power() == order.get_piece().get_power():
            # piece at landing is from the same power
            return 0
        else: # head-to-head or failed move at landing
            attack_strength = (0 if order.is_travel() else 1)
            power_at_landing = order_at_landing.get_piece().get_power()
            for support_order in self._get_real_supports(order):
                if (support_order.get_piece().get_power() != power_at_landing
                    and self._resolve(support_order, optimistic)
                ):
                    attack_strength += 1
            return max(0.5, attack_strength)
    
    def _get_support_strength(self, order, optimistic):
        support = 0
        for support_order in self._get_real_supports(order):
            if self._resolve(support_order, optimistic):
                support += 1
        return support
    
    # ==== Order retrieval ====
    
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
    
    def _get_move(self, square):
        for order in self.order_interface.get_orders():
            if not order.get_virtual() and isinstance(order, MoveOrder) and order.get_starting_square() == square:
                return order
        return None
    
    def _get_hold(self, square):
        """
        Get real hold order on `square`, if it exists. Note that all
        non-moving pieces get a real hold order.
        """
        for order in self.order_interface.get_orders():
            if isinstance(order, HoldOrder) and order.get_starting_square() == square:
                return order
        return None
    
    def _get_convoy(self, square):
        for order in self.order_interface.get_orders():
            if not order.get_virtual() and isinstance(order, ConvoyOrder) and order.get_starting_square() == square:
                return order
        return None
    
    def _get_order_at_landing(self, order):
        """
        Get order at the landing square. This is used when adjudicating move
        orders. In particular, we ignore convoy orders.
        """
        for other_order in self.order_interface.get_orders():
            if not isinstance(other_order, ConvoyOrder) and other_order.get_starting_square() == order.get_landing_square():
                return other_order
        return None
    
    def _get_real_supports(self, order):
        return [support_order for support_order in order.get_supports() if not support_order.get_virtual()]
    
    # ==== Debug messages ====
    
    def _debug_out(self, message):
        if self.verbose:
            print("│ " * self._debug_call_depth + message)
    
    def _debug_out_decr(self, message):
        if self.verbose:
            self._debug_call_depth -= 1
            print("│ " * self._debug_call_depth + "└ " + message)
    
    def _debug_optimistic(self, optimistic):
        return "optimistic" if optimistic else "pessimistic"
    
    def _debug_result(self, result):
        return "succeed" if result else "fail"
    
    def _debug_resolved(self, order):
        return "resolved" if self.resolved[order] else "unresolved"