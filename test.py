# -*-coding:utf8-*-

from chessdip.ui import GameManager
from chessdip.board import Power, Side
from chessdip.artists.palette import PowerPalette

# From the DATC
# 6. TEST CASES
# 6.A. TEST CASE, BASIC CHECKS
# 6.A.1. TEST CASE, BASIC MOVES
"""
Check that each piece can move where specified; check that they fail to move
where not specified. This can be improved/subdivided
"""
def test_6A1():
    GM.setup_pieces(england, ["Kd1", "Pd2", "Bc1", "Nb1", "Ra1"])
    GM.setup_pieces(italy, ["Ke1", "Bf1", "Ng1", "Rh1"])
    GM.setup_pieces(france, ["Pe7", "Ng8", "Rh8"])
    GM.setup_pieces(scandinavia, ["Kd8", "Pd7", "Bc8", "Nb8", "Ra8"])
    GM.process_orders(england, ["Kd1 d2", "Pd2 d4", "Bc1 b2", "Nb1 c3", "Ra1 a3"])
    GM.process_orders(italy, ["Ke1 e3", "Bf1 f2", "Ng1 g2", "Rh1 g3"])
    GM.process_orders(france, ["Pe7 e8", "Ng8 h7", "Rh8 g7"])
    GM.process_orders(scandinavia, ["Kd8 c7", "Pd7 d6", "Bc8 a6", "Nb8 d7", "Ra8 d8"])
    GM.adjudicate()

# 6.A.2. TEST CASE, MOVE ARMY TO SEA: not relevant
# 6.A.3. TEST CASE, MOVE FLEET TO LAND: not relevant
# 6.A.4. TEST CASE, MOVE TO OWN SECTOR
def test_6A4():
    GM.setup_pieces(england, ["Kd1"])
    GM.process_orders(england, ["Kd1 d1"])
    GM.adjudicate()

# 6.A.5. TEST CASE, MOVE TO OWN SECTOR WITH CONVOY: not possible
# 6.A.6. TEST CASE, ORDERING A UNIT OF ANOTHER COUNTRY
def test_6A6():
    GM.setup_pieces(england, ["Kd1"])
    GM.process_orders(italy, ["Kd1 d2"])
    GM.adjudicate()

# 6.A.7. TEST CASE, ONLY ARMIES CAN BE CONVOYED
"""
Modified: we check that convoy-supports only support convoys from valid pieces
"""
def test_6A7():
    GM.setup_pieces(england, ["Kd1"])
    GM.process_orders(england, ["Kd1 S d2 C b1 e3"])
    GM.adjudicate()

# 6.A.8. TEST CASE, SUPPORT TO HOLD YOURSELF IS NOT POSSIBLE
def test_6A8():
    GM.setup_pieces(england, ["Kd1"])
    GM.process_orders(england, ["Kd1 S d1 h"])
    GM.adjudicate()

# 6.A.9. TEST CASE, FLEETS MUST FOLLOW COAST IF NOT ON SEA: not relevant
# 6.A.10. TEST CASE, SUPPORT ON UNREACHABLE DESTINATION NOT POSSIBLE
def test_6A10():
    GM.setup_pieces(england, ["Kd1", "Rh1"])
    GM.process_orders(england, ["Rh1 H", "Kd1 S Rh1 H"])
    GM.adjudicate()

# 6.A.11. TEST CASE, SIMPLE BOUNCE
def test_6A11():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 d2"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.adjudicate()

# 6.A.12. TEST CASE, BOUNCE OF THREE UNITS
def test_6A12():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.setup_pieces(scandinavia, ["Pd3"])
    GM.process_orders(england, ["Kd1 d2"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.process_orders(scandinavia, ["Pd3 d2"])
    GM.adjudicate()

# 6.B. TEST CASES, COASTAL ISSUES
"""
Nothing here is relevant because there are no coasts
"""

# 6.C. TEST CASES, CIRCULAR MOVEMENT
# 6.C.1. TEST CASE, THREE ARMY CIRCULAR MOVEMENT
def test_6C1():
    GM.setup_pieces(england, ["Kd1", "Bd2", "Rc1"])
    GM.process_orders(england, ["Kd1 d2", "Bd2 c1", "Rc1 d1"])
    GM.adjudicate()

# 6.C.1.a. Different powers
def test_6C1A():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.setup_pieces(scandinavia, ["Rd2"])
    GM.process_orders(england, ["Kd1 e1"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.process_orders(scandinavia, ["Rd2 d1"])
    GM.adjudicate()

# 6.C.2. TEST CASE, THREE ARMY CIRCULAR MOVEMENT WITH SUPPORT
def test_6C2():
    GM.setup_pieces(england, ["Kd1", "Bd2", "Rc1", "Nc3"])
    GM.process_orders(england, ["Kd1 d2", "Bd2 c1", "Rc1 d1", "Nc3 S Rc1 d1"])
    GM.adjudicate()

# 6.C.3. TEST CASE, A DISRUPTED THREE ARMY CIRCULAR MOVEMENT
def test_6C3():
    GM.setup_pieces(england, ["Kd1", "Bd2", "Rc1", "Nc3"])
    GM.process_orders(england, ["Kd1 d2", "Bd2 c1", "Rc1 d1", "Nc3 d1"])
    GM.adjudicate()

# 6.C.4. TEST CASE, A CIRCULAR MOVEMENT WITH ATTACKED CONVOY
"""
Modified because convoys are automatically dislodged: here the convoy is
supported and attacked.
"""
def test_6C4():
    GM.setup_pieces(england, ["Ra1", "Ra3", "Bc1", "Nc3"])
    GM.setup_pieces(scandinavia, ["Bb3"])
    GM.process_orders(england, ["Ra1 c1", "Ra3 a1", "Bc1 a3", "Nc3 S a2 C Ra3 a1"])
    GM.process_orders(scandinavia, ["Bb3 a2"])
    GM.adjudicate()

# 6.C.5. TEST CASE, A DISRUPTED CIRCULAR MOVEMENT DUE TO DISLODGED CONVOY
def test_6C5():
    GM.setup_pieces(england, ["Ra1", "Ra3", "Bc1"])
    GM.setup_pieces(scandinavia, ["Bb3"])
    GM.process_orders(england, ["Ra1 c1", "Ra3 a1", "Bc1 a3"])
    GM.process_orders(scandinavia, ["Bb3 a2"])
    GM.adjudicate()

# 6.C.6. TEST CASE, TWO ARMIES WITH TWO CONVOYS: not possible
# 6.C.7. TEST CASE, DISRUPTED UNIT SWAP: not possible
# 6.C.8. TEST CASE, NO SELF DISLODGEMENT IN DISRUPTED CIRCULAR MOVEMENT
def test_6C8():
    GM.setup_pieces(england, ["Kd1", "Rd2", "Nc3"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.setup_pieces(scandinavia, ["Nc4"])
    GM.process_orders(england, ["Kd1 e1", "Rd2 d1", "Nc3 S Rd2 d1"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.process_orders(scandinavia, ["Nc4 d2"])
    GM.adjudicate()

# 6.C.9. TEST CASE, NO HELP IN DISLODGEMENT OF OWN UNIT IN DISRUPTED CIRCULAR MOVEMENT
def test_6C9():
    GM.setup_pieces(england, ["Kd1", "Nc3"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.setup_pieces(scandinavia, ["Rd2", "Nc4"])
    GM.process_orders(england, ["Kd1 e1", "Nc3 S Rd2 d1"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.process_orders(scandinavia, ["Rd2 d1", "Nc4 d2"])
    GM.adjudicate()

# 6.D. TEST CASES, SUPPORTS AND DISLODGES
# 6.D.1. TEST CASE, SUPPORTED HOLD CAN PREVENT DISLODGEMENT
def test_6D1():
    GM.setup_pieces(england, ["Kd1", "Nc2"])
    GM.setup_pieces(italy, ["Ke1", "Rh1"])
    GM.process_orders(england, ["Kd1 e1", "Nc2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 H", "Rh1 S Ke1 H"])
    GM.adjudicate()

# 6.D.2. TEST CASE, A MOVE CUTS SUPPORT ON HOLD
def test_6D2():
    GM.setup_pieces(england, ["Kd1", "Nc2", "Bf3"])
    GM.setup_pieces(italy, ["Ke1", "Rh1"])
    GM.process_orders(england, ["Kd1 e1", "Nc2 S Kd1 e1", "Bf3 h1"])
    GM.process_orders(italy, ["Ke1 H", "Rh1 S Ke1 H"])
    GM.adjudicate()

# 6.D.3. TEST CASE, A MOVE CUTS SUPPORT ON MOVE
def test_6D3():
    GM.setup_pieces(england, ["Kd1", "Nc2"])
    GM.setup_pieces(italy, ["Ke1", "Rh2"])
    GM.process_orders(england, ["Kd1 e1", "Nc2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 H", "Rh2 c2"])
    GM.adjudicate()

# 6.D.4. TEST CASE, SUPPORT TO HOLD ON UNIT SUPPORTING A HOLD ALLOWED
def test_6D4():
    GM.setup_pieces(england, ["Kd1", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Rh1", "Pe2"])
    GM.process_orders(england, ["Kd1 e2", "Nc3 S Kd1 e2"])
    GM.process_orders(italy, ["Ke1 S Pe2 H", "Rh1 S Ke1 H", "Pe2 H"])
    GM.adjudicate()

# 6.D.5. TEST CASE, SUPPORT TO HOLD ON UNIT SUPPORTING A MOVE ALLOWED
def test_6D5():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Bf1", "Rh1"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 S Bf1 e2", "Rh1 S Ke1 H", "Bf1 e2"])
    GM.adjudicate()

# 6.D.6. TEST CASE, SUPPORT TO HOLD ON CONVOYING UNIT ALLOWED
"""
Modified because convoys are weaker
"""
def test_6D6():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.process_orders(england, ["Kd1 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.adjudicate()

# 6.D.7. TEST CASE, SUPPORT TO HOLD ON MOVING UNIT NOT ALLOWED
def test_6D7():
    GM.setup_pieces(england, ["Kd1", "Nc3", "Bc1"])
    GM.setup_pieces(italy, ["Ke1", "Rh1", "Pe2"])
    GM.process_orders(england, ["Kd1 e2", "Nc3 S Kd1 e2", "Bc1 e3"])
    GM.process_orders(italy, ["Ke1 S Pe2 H", "Rh1 S Ke1 H", "Pe2 e3"])
    GM.adjudicate()

# 6.D.8. TEST CASE, FAILED CONVOY CANNOT RECEIVE HOLD SUPPORT
"""
Modified because convoys cannot be misordered
"""
def test_6D8():
    GM.setup_pieces(england, ["Ra1", "Nd2", "Ke2"])
    GM.setup_pieces(italy, ["Rh1", "Bf1"])
    GM.process_orders(england, ["Ra1 f1", "Nd2 S Ra1 f1", "Ke2 H"])
    GM.process_orders(italy, ["Rh1 S Bf1 H", "Bf1 d3"])
    GM.adjudicate()

# 6.D.9. TEST CASE, SUPPORT TO MOVE ON HOLDING UNIT NOT ALLOWED
def test_6D9():
    GM.setup_pieces(england, ["Kd1", "Nc3"])
    GM.setup_pieces(italy, ["Pe2", "Nf2"])
    GM.process_orders(england, ["Kd1 e2", "Nc3 S Kd1 e2"])
    GM.process_orders(italy, ["Pe2 H", "Nf2 S Pe2 e4"])
    GM.adjudicate()

# 6.D.10. TEST CASE, SELF DISLODGMENT PROHIBITED
def test_6D10():
    GM.setup_pieces(england, ["Kd1", "Ra1", "Nc3"])
    GM.process_orders(england, ["Kd1 H", "Ra1 d1", "Nc3 S Ra1 d1"])
    GM.adjudicate()

# 6.D.11. TEST CASE, NO SELF DISLODGMENT OF RETURNING UNIT
def test_6D11():
    GM.setup_pieces(england, ["Kd1", "Ra1", "Nc3"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 e2", "Ra1 d1", "Nc3 S Ra1 d1"])
    GM.process_orders(italy, ["Ke1 e2"])
    GM.adjudicate()

# 6.D.12. TEST CASE, SUPPORTING A FOREIGN UNIT TO DISLODGE OWN UNIT PROHIBITED
def test_6D12():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 H"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.adjudicate()

# 6.D.13. TEST CASE, SUPPORTING A FOREIGN UNIT TO DISLODGE A RETURNING OWN UNIT PROHIBITED
def test_6D13():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Pe2"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 e3"])
    GM.process_orders(italy, ["Ke1 d2", "Pe2 e3"])
    GM.adjudicate()

# 6.D.14. TEST CASE, SUPPORTING A FOREIGN UNIT IS NOT ENOUGH TO PREVENT DISLODGEMENT
def test_6D14():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 H"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.adjudicate()

# 6.D.15. TEST CASE, DEFENDER CANNOT CUT SUPPORT FOR ATTACK ON ITSELF
def test_6D15():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.adjudicate()

# 6.D.16. TEST CASE, CONVOYING A UNIT DISLODGING A UNIT OF SAME POWER IS ALLOWED: not relevant
# 6.D.17. TEST CASE, DISLODGEMENT CUTS SUPPORTS
def test_6D17():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3", "Rh1"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2", "Rh1 e1"])
    GM.adjudicate()

# 6.D.18. TEST CASE, A SURVIVING UNIT WILL SUSTAIN SUPPORT
def test_6D18():
    GM.setup_pieces(england, ["Kd1", "Bd2", "Nc4"])
    GM.setup_pieces(italy, ["Ke1", "Nf3", "Rh1"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1", "Nc4 S Bd2 H"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2", "Rh1 e1"])
    GM.adjudicate()

# 6.D.19. TEST CASE, EVEN WHEN SURVIVING IS IN ALTERNATIVE WAY
def test_6D19():
    GM.setup_pieces(england, ["Kd1", "Bd2", "Nc4"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1", "Nc4 S Ke1 D2"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.adjudicate()

# 6.D.20. TEST CASE, UNIT CANNOT CUT SUPPORT OF ITS OWN COUNTRY
def test_6D20():
    GM.setup_pieces(england, ["Be2"])
    GM.setup_pieces(italy, ["Ke1", "Bf1", "Rh1"])
    GM.process_orders(england, ["Be2 H"])
    GM.process_orders(italy, ["Ke1 e2", "Bf1 S Ke1 e2", "Rh1 f1"])
    GM.adjudicate()

# 6.D.21. TEST CASE, DISLODGING DOES NOT CANCEL A SUPPORT CUT
def test_6D21():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ke1", "Be2"])
    GM.setup_pieces(france, ["Re8"])
    GM.setup_pieces(scandinavia, ["Kd8", "Bd7"])
    GM.process_orders(england, ["Kd1 H"])
    GM.process_orders(italy, ["Ke1 d1", "Be2 S Ke1 d1"])
    GM.process_orders(france, ["Re8 e2"])
    GM.process_orders(scandinavia, ["Kd8 e8", "Bd7 S Kd8 e8"])
    GM.adjudicate()

# 6.D.22. TEST CASE, IMPOSSIBLE FLEET MOVE CANNOT BE SUPPORTED
"""
Replaced with impossible piece move in general
"""
def test_6D22():
    GM.setup_pieces(england, ["Ke2", "Nd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.process_orders(england, ["Ke2 f3", "Nd2 S Ke2 f3"])
    GM.process_orders(italy, ["Ke1 S Nf3 e2", "Nf3 e2"])
    GM.adjudicate()

# 6.D.23. TEST CASE, IMPOSSIBLE COAST MOVE CANNOT BE SUPPORTED: not relevant
# 6.D.24. TEST CASE, IMPOSSIBLE ARMY MOVE CANNOT BE SUPPORTED
"""
Just for the beleaguered garrison case
"""
def test_6D24():
    GM.setup_pieces(england, ["Ke2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(scandinavia, ["Bc4", "Nc3"])
    GM.process_orders(england, ["Ke2 H"])
    GM.process_orders(italy, ["Ke1 S Nf3 e2", "Nf3 e2"])
    GM.process_orders(scandinavia, ["Bc4 e2", "Nc3 S Bc4 e2"])
    GM.adjudicate()

# 6.D.25. TEST CASE, FAILING HOLD SUPPORT CAN BE SUPPORTED
def test_6D25():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 S Kd1 H", "Nf3 S Ke1 H"])
    GM.adjudicate()

# 6.D.26. TEST CASE, FAILING MOVE SUPPORT CAN BE SUPPORTED
def test_6D26():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 S Kd1 e2", "Nf3 S Ke1 H"])
    GM.adjudicate()

# 6.D.27. TEST CASE, FAILING CONVOY CAN BE SUPPORTED
"""
Actually we expect the opposite: a failing convoy cannot be supported.
"""
def test_6D27():
    GM.setup_pieces(england, ["Kd1", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.process_orders(england, ["Kd1 e2", "Nc3 S Kd1 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.adjudicate()

# 6.D.28. TEST CASE, IMPOSSIBLE MOVE AND SUPPORT
def test_6D28():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.setup_pieces(france, ["Re8"])
    GM.process_orders(england, ["Kd1 e1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 a8"])
    GM.process_orders(france, ["Re8 S Ke1 H"])
    GM.adjudicate()

# 6.D.29. TEST CASE, MOVE TO IMPOSSIBLE COAST AND SUPPORT: not relevant
# 6.D.30. TEST CASE, MOVE WITHOUT COAST AND SUPPORT: not relevant
# 6.D.31. TEST CASE, A TRICKY IMPOSSIBLE SUPPORT
"""
The original situation is not relevant because convoys are not explicitly
ordered. Here's another situation that maybe fits.
"""
def test_6D31():
    GM.setup_pieces(italy, ["Pe2", "Bf1"])
    GM.process_orders(italy, ["Pe2 S Bf1 d3", "Bf1 d3"])
    GM.adjudicate()

# 6.D.32. TEST CASE, A MISSING FLEET: not relevant
"""
Fleets cannot be missing in this variant
"""
# 6.D.33. TEST CASE, UNWANTED SUPPORT ALLOWED
def test_6D33():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(scandinavia, ["Nc2"])
    GM.process_orders(england, ["Kd1 S Ke1 e2"])
    GM.process_orders(italy, ["Ke1 e2", "Bf1 e2"])
    GM.process_orders(scandinavia, ["Nc2 e1"])
    GM.adjudicate()

# 6.D.34. TEST CASE, SUPPORT TARGETING OWN AREA NOT ALLOWED
def test_6D34():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(scandinavia, ["Kd2"])
    GM.process_orders(england, ["Kd1 d2", "Bc1 S Kd1 d2", "Nb1 S Kd1 d2"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.process_orders(scandinavia, ["Kd2 S Ke1 d2"])
    GM.adjudicate()

# 6.E. TEST CASES, HEAD-TO-HEAD BATTLES AND BELEAGUERED GARRISON
# 6.E.1. TEST CASE, DISLODGED UNIT HAS NO EFFECT ON ATTACKER'S AREA
def test_6E1():
    GM.setup_pieces(england, ["Kd1", "Ra1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 e1", "Ra1 d1", "Bd2 S Kd1 e1"])
    GM.process_orders(italy, ["Ke1 d1"])
    GM.adjudicate()

# 6.E.2. TEST CASE, NO SELF DISLODGEMENT IN HEAD-TO-HEAD BATTLE
def test_6E2():
    GM.setup_pieces(england, ["Kd1", "Rc1", "Nc3"])
    GM.process_orders(england, ["Kd1 c1", "Rc1 d1", "Nc3 S Rc1 d1"])
    GM.adjudicate()

# 6.E.3. TEST CASE, NO HELP IN DISLODGING OWN UNIT
def test_6E3():
    GM.setup_pieces(england, ["Kd1", "Nc3"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["Kd1 e1", "Nc3 S Ke1 d1"])
    GM.process_orders(italy, ["Ke1 d1"])
    GM.adjudicate()

# 6.E.4. TEST CASE, NON-DISLODGED LOSER STILL HAS EFFECT
def test_6E4():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1"])
    GM.setup_pieces(italy, ["Kd2", "Be2"])
    GM.setup_pieces(france, ["Rh1", "Nf2"])
    GM.setup_pieces(scandinavia, ["Kd3", "Bc3", "Nb3"])
    GM.process_orders(england, ["Kd1 d2", "Bc1 S Kd1 d2", "Nb1 S Kd1 d2"])
    GM.process_orders(italy, ["Kd2 d1", "Be2 S Kd2 d1"])
    GM.process_orders(france, ["Rh1 d1", "Nf2 S Rh1 d1"])
    GM.process_orders(scandinavia, ["Kd3 d2", "Bc3 S Kd3 d2", "Nb3 S Kd3 d2"])
    GM.adjudicate()

# 6.E.5. TEST CASE, LOSER DISLODGED BY ANOTHER ARMY STILL HAS EFFECT
def test_6E5():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1"])
    GM.setup_pieces(italy, ["Kd2", "Be2"])
    GM.setup_pieces(france, ["Rh1", "Nf2"])
    GM.setup_pieces(scandinavia, ["Kd3", "Bc3", "Nb3", "Ra2"])
    GM.process_orders(england, ["Kd1 d2", "Bc1 S Kd1 d2", "Nb1 S Kd1 d2"])
    GM.process_orders(italy, ["Kd2 d1", "Be2 S Kd2 d1"])
    GM.process_orders(france, ["Rh1 d1", "Nf2 S Rh1 d1"])
    GM.process_orders(scandinavia, ["Kd3 d2", "Bc3 S Kd3 d2", "Nb3 S Kd3 d2", "Ra2 S Kd3 d2"])
    GM.adjudicate()

# 6.E.6. TEST CASE, NOT DISLODGE BECAUSE OF OWN SUPPORT STILL HAS EFFECT
def test_6E6():
    GM.setup_pieces(england, ["Kd1", "Bc1"])
    GM.setup_pieces(italy, ["Kd2", "Be2", "Nf3"])
    GM.setup_pieces(france, ["Rh1", "Nf2"])
    GM.process_orders(england, ["Kd1 d2", "Bc1 S Kd1 d2"])
    GM.process_orders(italy, ["Kd2 d1", "Be2 S Kd2 d1", "Nf3 S Kd1 d2"])
    GM.process_orders(france, ["Rh1 d1", "Nf2 S Rh1 d1"])
    GM.adjudicate()

# 6.E.7. TEST CASE, NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON
def test_6E7():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(scandinavia, ["Bc3", "Nc4"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 H"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.process_orders(scandinavia, ["Bc3 d2", "Nc4 S Bc3 d2"])
    GM.adjudicate()

# 6.E.8. TEST CASE, NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON AND HEAD-TO-HEAD BATTLE
def test_6E8():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(scandinavia, ["Bc3", "Nc4"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 e1"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.process_orders(scandinavia, ["Bc3 d2", "Nc4 S Bc3 d2"])
    GM.adjudicate()

# 6.E.9. TEST CASE, ALMOST SELF DISLODGEMENT WITH BELEAGUERED GARRISON
def test_6E9():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(scandinavia, ["Bc3", "Nc4"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 e3"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.process_orders(scandinavia, ["Bc3 d2", "Nc4 S Bc3 d2"])
    GM.adjudicate()

# 6.E.10. TEST CASE, ALMOST CIRCULAR MOVEMENT WITH NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON
def test_6E10():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(scandinavia, ["Bc3", "Nc4", "Re3"])
    GM.process_orders(england, ["Kd1 S Ke1 d2", "Bd2 e3"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.process_orders(scandinavia, ["Bc3 d2", "Nc4 S Bc3 d2", "Re3 c3"])
    GM.adjudicate()

# 6.E.11. TEST CASE, NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON,
#         UNIT SWAP WITH ADJACENT CONVOYING AND TWO COASTS: not relevant
# 6.E.12. TEST CASE, SUPPORT ON ATTACK ON OWN UNIT CAN BE USED FOR OTHER MEANS
def test_6E12():
    GM.setup_pieces(england, ["Kd1", "Bd2"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(france, ["Re8"])
    GM.process_orders(england, ["Kd1 S Bd2 e1", "Bd2 e1"])
    GM.process_orders(italy, ["Ke1 d1", "Nf3 S Re8 e1"])
    GM.process_orders(france, ["Re8 e1"])
    GM.adjudicate()

# 6.E.13. TEST CASE, THREE WAY BELEAGUERED GARRISON
def test_6E13():
    GM.setup_pieces(england, ["Kd1", "Bc1"])
    GM.setup_pieces(italy, ["Ke1", "Nf3"])
    GM.setup_pieces(france, ["Kd2"])
    GM.setup_pieces(scandinavia, ["Kd3", "Bc3"])
    GM.process_orders(england, ["Kd1 d2", "Bc1 S Kd1 d2"])
    GM.process_orders(italy, ["Ke1 d2", "Nf3 S Ke1 d2"])
    GM.process_orders(france, ["Kd2 H"])
    GM.process_orders(scandinavia, ["Kd3 d2", "Bc3 S Kd3 d2"])
    GM.adjudicate()

# 6.E.14. TEST CASE, ILLEGAL HEAD-TO-HEAD BATTLE CAN STILL DEFEND
def test_6E14():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Ne2"])
    GM.process_orders(england, ["Kd1 e2"])
    GM.process_orders(italy, ["Ne2 d1"])
    GM.adjudicate()

# 6.E.15. TEST CASE, THE FRIENDLY HEAD-TO-HEAD BATTLE
def test_6E15():
    GM.setup_pieces(england, ["Kd1", "Bc1"])
    GM.setup_pieces(italy, ["Kd2", "Be2", "Nf2"])
    GM.setup_pieces(france, ["Kd4", "Be4"])
    GM.setup_pieces(scandinavia, ["Kd3", "Bc3", "Nb3"])
    GM.process_orders(england, ["Kd1 d2", "Bc1 S Kd1 d2"])
    GM.process_orders(italy, ["Kd2 d3", "Be2 S Kd2 d3", "Nf2 S Kd2 d3"])
    GM.process_orders(france, ["Kd4 d3", "Be4 S Kd4 d3"])
    GM.process_orders(scandinavia, ["Kd3 d2", "Bc3 S Kd3 d2", "Nb3 S Kd3 d2"])
    GM.adjudicate()

# 6.F. TEST CASES, CONVOYS
# 6.F.1. TEST CASE, NO CONVOY IN COASTAL AREAS: not relevant
# 6.F.2. TEST CASE, AN ARMY BEING CONVOYED CAN BOUNCE AS NORMAL
def test_6F2():
    GM.setup_pieces(england, ["Pd2"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.process_orders(england, ["Pd2 d3"])
    GM.process_orders(italy, ["Bf1 d3"])
    GM.adjudicate()

# 6.F.3. TEST CASE, AN ARMY BEING CONVOYED CAN RECEIVE SUPPORT
def test_6F3():
    GM.setup_pieces(england, ["Pd2"])
    GM.setup_pieces(italy, ["Bf1", "Nf2"])
    GM.process_orders(england, ["Pd2 d3"])
    GM.process_orders(italy, ["Bf1 d3", "Nf2 S Bf1 d3"])
    GM.adjudicate()

# 6.F.4. TEST CASE, AN ATTACKED CONVOY IS NOT DISRUPTED
"""
We expect the opposite in this variant
"""
def test_6F4():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.process_orders(england, ["Kd1 e2"])
    GM.process_orders(italy, ["Bf1 d3"])
    GM.adjudicate()

# 6.F.5. TEST CASE, A BELEAGUERED CONVOY IS NOT DISRUPTED
def test_6F5():
    GM.setup_pieces(england, ["Kd1"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.setup_pieces(france, ["Re8"])
    GM.process_orders(england, ["Kd1 e2"])
    GM.process_orders(italy, ["Bf1 d3"])
    GM.process_orders(france, ["Re8 e2"])
    GM.adjudicate()

# 6.F.6. TEST CASE, DISLODGED CONVOY DOES NOT CUT SUPPORT
def test_6F6():
    GM.setup_pieces(england, ["Kd1", "Nd3", "Nb2"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.setup_pieces(scandinavia, ["Rb3", "Bc3"])
    GM.process_orders(england, ["Kd1 e2", "Nd3 S Nb2 H", "Nb2 S Bd3 H"])
    GM.process_orders(italy, ["Bf1 d3"])
    GM.process_orders(scandinavia, ["Rb3 b2", "Bc3 S Rb3 b2"])
    GM.adjudicate()

# 6.F.7. TEST CASE, DISLODGED CONVOY DOES NOT CAUSE CONTESTED AREA
"""
Not relevant, due to there being no retreats
"""
# 6.F.8. TEST CASE, DISLODGED CONVOY DOES NOT CAUSE A BOUNCE
def test_6F8():
    GM.setup_pieces(england, ["Kd1", "Pd2"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.process_orders(england, ["Kd1 e2", "Pd2 d3"])
    GM.process_orders(italy, ["Bf1 d3"])
    GM.adjudicate()

# 6.F.9. TEST CASE, DISLODGE OF MULTI-ROUTE CONVOY: not relevant
"""
There are never multiple convoy routes for the same move
"""
# 6.F.10. TEST CASE, DISLODGE OF MULTI-ROUTE CONVOY WITH FOREIGN FLEET: not relevant
# 6.F.11. TEST CASE, DISLODGE OF MULTI-ROUTE CONVOY WITH ONLY FOREIGN FLEETS: not relevant
# 6.F.12. TEST CASE, DISLODGED CONVOYING FLEET NOT ON ROUTE: not relevant
# 6.F.13. TEST CASE, THE UNWANTED ALTERNATIVE: not relevant
# 6.F.14. TEST CASE, SIMPLE CONVOY PARADOX
"""
Modified due to weaker convoys
"""
def test_6F14():
    GM.setup_pieces(england, ["Kd3", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.process_orders(england, ["Kd3 S Nc3 e2", "Nc3 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.adjudicate()

def test_6F14A(): # simple version
    GM.setup_pieces(england, ["Kd3"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.process_orders(england, ["Kd3 e2"])
    GM.process_orders(italy, ["Bf1 d3"])
    GM.adjudicate()

def test_6F14B(): # swapped move-support
    GM.setup_pieces(england, ["Kd3", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.process_orders(england, ["Kd3 e2", "Nc3 S Kd3 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.adjudicate()

"""
These convoy paradoxes sort of merge with support cutting rules...
Bf1 dislodges Kd3, so it successfully cuts the support of Kd3 for Nc3 e2?

"""
def test_6F14C(): # extra support on convoyed move
    GM.setup_pieces(england, ["Kd3", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1", "Nf2"])
    GM.process_orders(england, ["Kd3 S Nc3 e2", "Nc3 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3", "Nf2 S Bf1 d3"])
    GM.adjudicate()

# 6.F.15. TEST CASE, SIMPLE CONVOY PARADOX WITH ADDITIONAL CONVOY
def test_6F15():
    GM.setup_pieces(england, ["Kd3", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Bh8"])
    GM.process_orders(england, ["Kd3 S Nc3 e2", "Nc3 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Bh8 c3"])
    GM.adjudicate()

# 6.F.16. TEST CASE, PANDIN'S PARADOX
def test_6F16():
    GM.setup_pieces(england, ["Kd3", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Ke3", "Bf3"])
    GM.process_orders(england, ["Kd3 S Nc3 e2", "Nc3 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Ke3 S Bf3 e2", "Bf3 e2"])
    GM.adjudicate()

# 6.F.17. TEST CASE, PANDIN'S EXTENDED PARADOX
def test_6F17():
    GM.setup_pieces(england, ["Kd3", "Nc3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1", "Nf2"])
    GM.setup_pieces(france, ["Ke3", "Bf3"])
    GM.process_orders(england, ["Kd3 S Nc3 e2", "Nc3 e2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3", "Nf2 S Bf1 d3"])
    GM.process_orders(france, ["Ke3 S Bf3 e2", "Bf3 e2"])
    GM.adjudicate()

# 6.F.18. TEST CASE, BETRAYAL PARADOX
"""
Doesn't really work the same because support-convoys explicitly state the
convoy path. The convoy fails, but in this variant this makes the support-
convoys fail as well, so Bf3 e2 succeeds.
"""
def test_6F18():
    GM.setup_pieces(england, ["Kd3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Ke3", "Bf3"])
    GM.process_orders(england, ["Kd3 S e2 C Bf1 d3"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Ke3 S Bf3 e2", "Bf3 e2"])
    GM.adjudicate()

def test_6F18A(): # dislodging a supported convoy
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Ke3", "Bf3"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Ke3 S Bf3 e2", "Bf3 e2"])
    GM.adjudicate()

# 6.F.19. TEST CASE, MULTI-ROUTE CONVOY DISRUPTION PARADOX: not relevant
# 6.F.20. TEST CASE, UNWANTED MULTI-ROUTE CONVOY PARADOX: not relevant
# 6.F.21. TEST CASE, DAD'S ARMY CONVOY
def test_6F21():
    GM.setup_pieces(england, ["Kd1", "Nc3"])
    GM.setup_pieces(italy, ["Kd3", "Bf1"])
    GM.setup_pieces(france, ["Be4", "Nf4"])
    GM.process_orders(england, ["Kd1 e2", "Nc3 S Kd1 e2"])
    GM.process_orders(italy, ["Kd3 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Be4 d3", "Nf4 S Be4 d3"])
    GM.adjudicate()

# 6.F.22. TEST CASE, SECOND ORDER PARADOX WITH TWO RESOLUTIONS
def test_6F22():
    GM.setup_pieces(england, ["Kd2", "Rc1"])
    GM.setup_pieces(italy, ["Ke1", "Rf2"])
    GM.setup_pieces(france, ["Kd3", "Re4"])
    GM.setup_pieces(scandinavia, ["Kc4", "Rb3"])
    GM.process_orders(england, ["Kd2 S Rc1 c3", "Rc1 c3"])
    GM.process_orders(italy, ["Ke1 S e2 C Rf2 d2", "Rf2 d2"])
    GM.process_orders(france, ["Kd3 S Re4 e2", "Re4 e2"])
    GM.process_orders(scandinavia, ["Kc4 S c3 C Rb3 d3", "Rb3 d3"])
    GM.adjudicate()

# 6.F.23. TEST CASE, SECOND ORDER PARADOX WITH TWO EXCLUSIVE CONVOYS
def test_6F23():
    GM.setup_pieces(england, ["Kd2", "Rc1"])
    GM.setup_pieces(italy, ["Ke1", "Rf2", "Bb4"])
    GM.setup_pieces(france, ["Kd3", "Re4"])
    GM.setup_pieces(scandinavia, ["Kc4", "Rb3", "Bf3"])
    GM.process_orders(england, ["Kd2 S Rc1 c3", "Rc1 c3"])
    GM.process_orders(italy, ["Ke1 S e2 C Rf2 d2", "Rf2 d2", "Bb4 S c3 C Rb3 d3"])
    GM.process_orders(france, ["Kd3 S Re4 e2", "Re4 e2"])
    GM.process_orders(scandinavia, ["Kc4 S c3 C Rb3 d3", "Rb3 d3", "Bf3 S e2 C Rf2 d2"])
    GM.adjudicate()

# 6.F.24. TEST CASE, SECOND ORDER PARADOX WITH NO RESOLUTION
def test_6F24():
    GM.setup_pieces(england, ["Kd1", "Nd3", "Be3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Bg3", "Nh3"])
    GM.process_orders(england, ["Kd1 e2", "Nd3 S Be3 f2", "Be3 f2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Bg3 e1", "Nh3 S f2 C Bg3 e1"])
    GM.adjudicate()

def test_6F24A():
    GM.setup_pieces(england, ["Nd3", "Be3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Bg3", "Nh3"])
    GM.process_orders(england, ["Nd3 S Be3 f2", "Be3 f2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Bg3 e1", "Nh3 S f2 C Bg3 e1"])
    GM.adjudicate()

def test_6F24B():
    GM.setup_pieces(england, ["Kd1", "Nd3", "Be3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Bg3", "Nh3", "Ng2"])
    GM.process_orders(england, ["Kd1 e2", "Nd3 S Be3 f2", "Be3 f2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Bg3 e1", "Nh3 S f2 C Bg3 e1", "Ng2 S Bg3 e1"])
    GM.adjudicate()

def test_6F24C():
    GM.setup_pieces(england, ["Nd3", "Be3"])
    GM.setup_pieces(italy, ["Ke1", "Bf1"])
    GM.setup_pieces(france, ["Bg3", "Nh3", "Ng2"])
    GM.process_orders(england, ["Nd3 S Be3 f2", "Be3 f2"])
    GM.process_orders(italy, ["Ke1 S e2 C Bf1 d3", "Bf1 d3"])
    GM.process_orders(france, ["Bg3 e1", "Nh3 S f2 C Bg3 e1", "Ng2 S Bg3 e1"])
    GM.adjudicate()

# 6.F.25. TEST CASE, CUT SUPPORT LAST
"""
A failed convoy that sufficiently protects itself should be able to cut...
"""
def test_6F25():
    GM.setup_pieces(england, ["Kd1", "Bc4", "Nb2"])
    GM.setup_pieces(italy, ["Ke1", "Be2", "Rf1", "Nh1"])
    GM.setup_pieces(france, ["Kg3", "Nf4", "Bf5"])
    GM.process_orders(england, ["Kd1 H", "Bc4 e2", "Nb2 S d3 C Bc4 e2"])
    GM.process_orders(italy, ["Ke1 d1", "Be2 S Ke1 d1", "Rf1 f4", "Nh1 S f2 C Rf1 f4"])
    GM.process_orders(france, ["Kg3 f2", "Bf5 d3", "Nf4 S Bf5 d3"])
    GM.adjudicate()

# 6.G. TEST CASES, CONVOYING TO ADJACENT PROVINCES
"""
Not possible due to the way that (1) convoys are implicitly ordered and
(2) convoys are never ambiguous or redundant.
"""

# 6.H. TEST CASES, RETREATING
"""
Not relevant, since dislodged pieces are automatically disbanded.
"""

# 6.I. TEST CASES, BUILDING
"""
To do
"""

# 6.J. TEST CASES, CIVIL DISORDER AND DISBANDS
"""
To do
"""

# CD.T. TEST CASES, CHESS DIP SPECIFIC CASES
# CD.T.1. TEST CASE, CROSSING CONVOYS
def test_CDT1():
    GM.setup_pieces(england, ["Bb1"])
    GM.setup_pieces(italy, ["Bf1"])
    GM.process_orders(england, ["Bb1 e4"])
    GM.process_orders(italy, ["Bf1 c4"])
    GM.adjudicate()

# CD.T.2. TEST CASE, CIRCULAR CONVOY SUPPORT
def test_CDT2():
    GM.setup_pieces(england, ["Rc2"])
    GM.setup_pieces(italy, ["Re1"])
    GM.setup_pieces(france, ["Bf4"])
    GM.process_orders(england, ["Rc2 S e2 C Re1 S e3"])
    GM.process_orders(italy, ["Re1 S e3 C Bf4 S d2"])
    GM.process_orders(france, ["Bf4 S d2 C Rc2 S e2"])
    GM.adjudicate()

# CD.T.3. TEST CASE, ATTACKED CIRCULAR CONVOY SUPPORT
def test_CDT2():
    GM.setup_pieces(england, ["Rc2"])
    GM.setup_pieces(italy, ["Re1"])
    GM.setup_pieces(france, ["Bf4"])
    GM.setup_pieces(scandinavia, ["Kd4"])
    GM.process_orders(england, ["Rc2 S e2 C Re1 S e3"])
    GM.process_orders(italy, ["Re1 S e3 C Bf4 S d2"])
    GM.process_orders(france, ["Bf4 S d2 C Rc2 S e2"])
    GM.process_orders(scandinavia, ["Kd4 e3"])
    GM.adjudicate()

# CD.T.3. TEST CASE, DISRUPTED CIRCULAR CONVOY SUPPORT
def test_CDT3():
    GM.setup_pieces(england, ["Rc2"])
    GM.setup_pieces(italy, ["Re1"])
    GM.setup_pieces(france, ["Bf4"])
    GM.setup_pieces(scandinavia, ["Kd4", "Nc4"])
    GM.process_orders(england, ["Rc2 S e2 C Re1 S e3"])
    GM.process_orders(italy, ["Re1 S e3 C Bf4 S d2"])
    GM.process_orders(france, ["Bf4 S d2 C Rc2 S e2"])
    GM.process_orders(scandinavia, ["Kd4 e3", "Nc4 S Kd4 e3"])
    GM.adjudicate()

# CD.T.4. TEST CASE, MULTIPLE CONVOYS FOR A MOVE
def test_CDT4():
    GM.setup_pieces(england, ["Ra1"])
    GM.process_orders(england, ["Ra1 a8"])
    GM.adjudicate()

# CD.T.5. TEST CASE, BLOCKED CONVOY
def test_CDT5():
    GM.setup_pieces(england, ["Ra1", "Pa4"])
    GM.process_orders(england, ["Ra1 a8", "Pa4 H"])
    GM.adjudicate()

# CD.T.5. TEST CASE, FAILED SUPPORT CONVOY
def test_CDT6():
    GM.setup_pieces(england, ["Ra1", "Pa4", "Bd2"])
    GM.setup_pieces(scandinavia, ["Kb6"])
    GM.process_orders(england, ["Ra1 a8", "Pa4 H", "Bd2 S a5 C Ra1 a8"])
    GM.process_orders(scandinavia, ["Kb6 a5"])
    GM.adjudicate()

# CD.T.7. TEST CASE, MOVING PIECE DOES NOT DISRUPT CONVOY
def test_CDT7():
    GM.setup_pieces(italy, ["Bf1", "Pe2"])
    GM.process_orders(italy, ["Bf1 d3", "Pe2 e4"])
    GM.adjudicate()

# CD.T.8. TEST CASE, SUPPORTING PIECE ON CONVOY PATH FAILS IN SOME CASES
def test_CDT8():
    GM.setup_pieces(france, ["Pe7"])
    GM.setup_pieces(scandinavia, ["Bc8", "Pd7"])
    GM.process_orders(france, ["Pe7 e6"])
    GM.process_orders(scandinavia, ["Bc8 S Pd7 e6", "Pd7 e6"])
    GM.adjudicate()

def test_CDT8A():
    GM.setup_pieces(france, ["Pe7"])
    GM.setup_pieces(scandinavia, ["Bc8", "Pd7"])
    GM.process_orders(france, ["Pe7 H"])
    GM.process_orders(scandinavia, ["Bc8 S Pd7 e6", "Pd7 e6"])
    GM.adjudicate()

# CD.T.9. TEST CASE, KINGSIDE CASTLE
def test_CDT9():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.setup_pieces(italy, ["Ke1", "Rh1"])
    GM.setup_pieces(france, ["Ke8", "Rh8"])
    GM.setup_pieces(scandinavia, ["Kd8", "Ra8"])
    GM.process_orders(england, ["O-O"])
    GM.process_orders(italy, ["O-O"])
    GM.process_orders(france, ["O-O"])
    GM.process_orders(scandinavia, ["O-O"])

# CD.T.10. TEST CASE, QUEENSIDE CASTLE
def test_CDT10():
    GM.setup_pieces(england, ["Kd1", "Rh1"])
    GM.setup_pieces(france, ["Ke8", "Ra8"])
    GM.process_orders(england, ["O-O-O"])
    GM.process_orders(france, ["O-O-O"])

def test_CDT10A():
    GM.setup_pieces(italy, ["Ke1", "Ra1"])
    GM.setup_pieces(scandinavia, ["Kd8", "Rh8"])
    GM.process_orders(italy, ["O-O-O"])
    GM.process_orders(scandinavia, ["O-O-O"])

# CD.T.11. TEST CASE, INTERRUPTED CASTLE
def test_CDT11():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.setup_pieces(scandinavia, ["Kc2"])
    GM.process_orders(england, ["O-O"])
    GM.process_orders(scandinavia, ["Kc2 c1"])
    GM.adjudicate()

# CD.T.12. TEST CASE, SUPPORTED CASTLE WILL BOUNCE
def test_CDT12():
    GM.setup_pieces(england, ["Kd1", "Ra1", "Bd2"])
    GM.setup_pieces(scandinavia, ["Kc2"])
    GM.process_orders(england, ["O-O", "Bd2 S Ra1 c1"])
    GM.process_orders(scandinavia, ["Kc2 c1"])
    GM.adjudicate()

# CD.T.13. TEST CASE, SUFFICIENTLY SUPPORTED CASTLE SUCCEEDS
def test_CDT13():
    GM.setup_pieces(england, ["Kd1", "Ra1", "Bd2", "Nb3"])
    GM.setup_pieces(scandinavia, ["Kc2"])
    GM.process_orders(england, ["O-O", "Bd2 S Ra1 c1", "Nb3 S Ra1 c1"])
    GM.process_orders(scandinavia, ["Kc2 c1"])
    GM.adjudicate()

# CD.T.14. TEST CASE, INTERRUPTED PAWN ADVANCE
def test_CDT14():
    GM.setup_pieces(england, ["Pc2"])
    GM.setup_pieces(scandinavia, ["Rc8"])
    GM.process_orders(england, ["Pc2 c3"])
    GM.process_orders(scandinavia, ["Rc8 c3"])
    GM.adjudicate()

# CD.T.15. TEST CASE, SUPPORTED PAWN ADVANCE WILL BOUNCE
def test_CDT15():
    GM.setup_pieces(england, ["Pc2", "Nb1"])
    GM.setup_pieces(scandinavia, ["Rc8"])
    GM.process_orders(england, ["Pc2 c3", "Nb1 S Pc2 c3"])
    GM.process_orders(scandinavia, ["Rc8 c3"])
    GM.adjudicate()

# CD.T.16. TEST CASE, SUFFICIENTLY SUPPORTED PAWN ADVANCE SUCCEEDS
def test_CDT16():
    GM.setup_pieces(england, ["Pc2", "Nb1", "Kd2"])
    GM.setup_pieces(scandinavia, ["Rc8"])
    GM.process_orders(england, ["Pc2 c3", "Nb1 S Pc2 c3", "Kd2 S Pc2 c3"])
    GM.process_orders(scandinavia, ["Rc8 c3"])
    GM.adjudicate()

# CD.T.17. TEST CASE, IMPOSSIBLE CASTLE
def test_CDT17():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.setup_pieces(scandinavia, ["Kc1"])
    GM.process_orders(england, ["O-O"])
    GM.process_orders(scandinavia, ["Kc1 b1"])
    GM.adjudicate()

# CD.T.18. TEST CASE, SUPPORTED CASTLE CAN DISLODGE
def test_CDT18():
    GM.setup_pieces(england, ["Kd1", "Ra1", "Bd2", "Nc3"])
    GM.setup_pieces(italy, ["Bd3", "Ne2"])
    GM.setup_pieces(scandinavia, ["Kc1"])
    GM.process_orders(england, ["O-O", "Bd2 S Ra1 c1", "Nc3 S Kd1 b1"])
    GM.process_orders(italy, ["Bd3 S Kd1 b1", "Ne2 S Ra1 c1"])
    GM.process_orders(scandinavia, ["Kc1 b1"])
    GM.adjudicate()

# CD.T.19. TEST CASE, CASTLE CIRCULAR MOVEMENT
def test_CDT19():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.setup_pieces(scandinavia, ["Kc1"])
    GM.process_orders(england, ["O-O"])
    GM.process_orders(scandinavia, ["Kc1 d1"])
    GM.adjudicate()

# CD.T.20. TEST CASE, CASTLE DOUBLE CIRCULAR MOVEMENT
def test_CDT20():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.setup_pieces(scandinavia, ["Kd2", "Rc1", "Bc3", "Nb1"])
    GM.process_orders(england, ["O-O"])
    GM.process_orders(scandinavia, ["Kd2 d1", "Rc1 c3", "Bc3 a1", "Nb1 d2"])
    GM.adjudicate()

# CD.T.21. TEST CASE, CASTLE DOUBLE CIRCULAR MOVEMENT, ONE FAILURE IMPLIES THE OTHER
def test_CDT21():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.setup_pieces(scandinavia, ["Kd2", "Rc1", "Bc3", "Nb1"])
    GM.setup_pieces(italy, ["Ke1"])
    GM.process_orders(england, ["O-O"])
    GM.process_orders(scandinavia, ["Kd2 d1", "Rc1 c3", "Bc3 a1", "Nb1 d2"])
    GM.process_orders(italy, ["Ke1 d2"])
    GM.adjudicate()

# CD.T.22. TEST CASE, EN PASSANT
def test_CDT22():
    GM.setup_pieces(england, ["Pd5", "Ba3"])
    GM.setup_pieces(scandinavia, ["Pc7"])
    GM.process_orders(scandinavia, ["Pc7 c5"])
    GM.progress()
    GM.process_orders(england, ["Pd5 t c6 x c5", "Ba3 S Pd5 x c5"])
    GM.adjudicate()

# CD.T.23. TEST CASE, BLOCKING EN PASSANT
def test_CDT23():
    GM.setup_pieces(england, ["Pd5", "Ba3"])
    GM.setup_pieces(scandinavia, ["Pc7"])
    GM.process_orders(scandinavia, ["Pc7 c5"])
    GM.progress()
    GM.process_orders(scandinavia, ["Nb8 c6"])
    GM.process_orders(england, ["Pd5 t c6 x c5", "Ba3 S Pd5 x c5"])
    GM.adjudicate()

# CD.T.24. TEST CASE, EN PASSANT REQUIRES TWO PHASES
def test_CDT24():
    GM.setup_pieces(england, ["Pd5", "Ba3"])
    GM.setup_pieces(scandinavia, ["Pc7", "Nb8"])
    GM.process_orders(england, ["Pd5 t c6 x c5", "Ba3 S Pd5 x c5"])
    GM.process_orders(scandinavia, ["Pc7 c5"])
    GM.adjudicate()

# CD.T.25. TEST CASE, EN PASSANT REQUIRES TWO CONSECUTIVE PHASES
def test_CDT25():
    GM.setup_pieces(england, ["Pd5", "Ba3"])
    GM.setup_pieces(scandinavia, ["Pc7"])
    GM.process_orders(scandinavia, ["Pc7 c5"])
    GM.progress()
    GM.progress()
    GM.process_orders(england, ["Pd5 t c6 x c5", "Ba3 S Pd5 x c5"])
    GM.adjudicate()

# CD.T.26. TEST CASE, PAWN CANNOT TRAVEL WITHOUT DISLODGING
def test_CDT26():
    GM.setup_pieces(italy, ["Bc4", "Pe4"])
    GM.setup_pieces(scandinavia, ["Pc6"])
    GM.process_orders(italy, ["Bc4 S Pe4 d5", "Pe4 d5"])
    GM.process_orders(scandinavia, ["Pc6 d5"])
    GM.adjudicate()

# CD.V. CHESS DIP VISUALIZER TESTS
# CD.V.1. VISUAL TEST, OVERLAPPING SUPPORTS
def test_CDV1():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1", "Ra2", "Be3"])
    GM.process_orders(england, ["Kd1 S Be3 d2", "Bc1 S Be3 d2", "Nb1 S Be3 d2", "Ra2 S Be3 d2", "Be3 d2"])

def test_CDV1A():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1", "Ra2", "Be1"])
    GM.setup_pieces(italy, ["Rh2"])
    GM.process_orders(england, ["Kd1 S Be1 d2", "Bc1 S Be1 d2", "Nb1 S Be1 d2", "Ra2 S Be1 d2", "Be1 d2"])
    GM.process_orders(italy, ["Rh2 S Ra2 H"])

def test_CDV1B():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1", "Ra2", "Bc3"])
    GM.process_orders(england, ["Kd1 S Bc3 d2", "Bc1 S Bc3 d2", "Nb1 S Bc3 d2", "Ra2 S Bc3 d2", "Bc3 d2"])

def test_CDV1C():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1", "Ra2", "Re2"])
    GM.process_orders(england, ["Kd1 S Re2 d2", "Bc1 S Re2 d2", "Nb1 S Re2 d2", "Ra2 S Re2 d2", "Re2 d2"])

def test_CDV1D():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1", "Ra2", "Rd3"])
    GM.process_orders(england, ["Kd1 S Rd3 d2", "Bc1 S Rd3 d2", "Nb1 S Rd3 d2", "Ra2 S Rd3 d2", "Rd3 d2"])


# CD.V.2. VISUAL TEST, OPPOSING MOVEMENT
def test_CDV2():
    GM.setup_pieces(england, ["Kd1", "Ra1"])
    GM.process_orders(england, ["Kd1 c1", "Ra1 e1"])

# CD.V.3. VISUAL TEST, ALL PIECES
def test_CDV3():
    GM.setup_pieces(england, ["Kd1", "Bc1", "Nb1", "Ra1", "Pd2", "Pc2", "Pb2", "Pa2"])
    GM.setup_pieces(italy, ["Ke1", "Bf1", "Ng1", "Rh1", "Pe2", "Pf2", "Pg2", "Ph2"])
    GM.setup_pieces(france, ["Ke8", "Bf8", "Ng8", "Rh8", "Pe7", "Pf7", "Pg7", "Ph7"])
    GM.setup_pieces(scandinavia, ["Kd8", "Bc8", "Nb8", "Ra8", "Pd7", "Pc7", "Pb7", "Pa7"])

def test():
    GM.visualizer.ion()
    GM.visualizer.show()
    while True:
        GM.visualizer.render()
        message = GM.console.input("> ").lower().replace(' ','')
        if not message:
            continue
        if message == "quit":
            return
        elif message == "clear":
            GM.clear_board()
        elif message == "progress":
            GM.progress()
        else: # find test and run it
            if len(message) < 2:
                continue
            elif message[0] == '6':
                message = message[1:]
            elif message[:1] == "cd":
                message = message[2:]
            
            if len(message) < 2:
                continue
            elif message[0] in "abcdefghij" and message[1].isnumeric():
                message = "6" + message
            elif message[0] in "tv" and message[1].isnumeric():
                message = "cd" + message
            
            GM.clear_board()
            # try:
            eval(f"test_{message.upper()}()")
            GM.sandbox()
            # except NameError as inst:
            #     GM.console.out(f"Could not find test {message}! {inst}")
            # except ValueError as inst:
            #     GM.console.out(f"yeah, {inst}")


def sandbox():
    GM.setup_pieces(england, ["K d1", "P c2", "N b1", "Ra1"])
    GM.setup_pieces(italy, ["K e1", "P e2", "B f1", "Rh1"])
    GM.setup_pieces(france, ["K e8", "P e7", "N g8", "Rh8"])
    GM.setup_pieces(scandinavia, ["K d8", "P d7", "B c8", "Ra8"])
    GM.sandbox()

red = PowerPalette("darkred", "indianred", "firebrick", "lightsalmon", "mistyrose")
green = PowerPalette("darkgreen", "forestgreen", "xkcd:green", "lightgreen", "honeydew")
blue = PowerPalette("midnightblue", "steelblue", "royalblue", "lightskyblue", "aliceblue")
yellow = PowerPalette("saddlebrown", "darkgoldenrod", "goldenrod", "palegoldenrod", "lightyellow")
GM = GameManager()
GM.console.out("Run DATC tests.")
england = GM.add_power("England", red, Side.WHITE, d_king=True)
italy = GM.add_power("Italy", green, Side.WHITE)
france = GM.add_power("France", blue, Side.BLACK)
scandinavia = GM.add_power("Scandinavia", yellow, Side.BLACK, d_king=True)
    

if __name__ == "__main__":
    test()
    # sandbox()
    
    