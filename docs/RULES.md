# Appetizer

**Chess Dip** is Diplomacy played on a chess board. The mechanics are a balance of Diplomacy rules, chess moves, and interesting strategy. Each side of the board is divided into two powers, named after a classic chess opening or defense. Units are all possible chess pieces except for the queen. Pieces move and support following their chess moves: this includes [castling](#castling) and [en passant](#en-passant)\! Also, dislodged pieces are automatically disbanded.

The major novelty is the introduction of [multiple-square orders](#bishops-and-rooks-introducing-multiple-square-orders), like those of bishops and rooks (but not knights\!). Much like a convoy, for these orders to succeed, no intermediate square may be “dislodged”. To prevent dislodges, intermediate squares may be supported by a new move called support-convoying, similar to support-holds. Both multiple-square moves and multiple-square supports are allowed. Multiple-square supports may themselves be supported, and so on. If an intermediate square is dislodged, then all support-convoys on later squares in the multiple-square order fail.

# Main course: the rules

After describing the basic board and game setup, we progressively introduce pieces and mechanisms in a somewhat informal manner. The formal rules are found in the [next section](#dessert-an-axiomatic-approach).

## Setup
### Board and win condition

The map is an 8 by 8 grid of squares called the **board**. Rows are called **rank**s, labeled `1` through `8`; columns are called **file**s, labeled `a` through `h`. Thus the squares have names such as `a1`, `h8`, and so on.
There are 29 supply centers; the win condition is owning 15 of them.

### Powers

There are four powers: England (quartz), Italy (opal), France (obsidian), and Scandinavia (onyx).

### Units

The units are called pieces. There are pawns, bishops, knights, rooks, and kings. Note that there are no queens.

### Starting positions

Each power starts with a king, a pawn, and either a knight or a bishop.

### Game structure

The game plays out like in standard Diplomacy: there are two seasons and a build phase every year.

## Kings and knights: a standard variant

Kings and knights move as they do in chess on an empty board; see the variant [Chesspolitik](https://nopunin10did.com/chesspolitik/). Their supports follow the same paths, and adjudication follows standard Diplomacy rules. Note that kings may move “into check” and hold while “under check”.

### Orders

Here are some examples of orders:

> move: `Ke1 - e2`  
> hold: `Kd1 H`  
> support-move: `Ng1 S e1 - e2`  
> support-hold: `Nc3 S d1 H`

### Dislodges

Dislodged pieces are automatically disbanded. We slightly modify the definition of dislodging for reasons that will be clear when pawns are introduced: a piece is dislodged when it does not or fails to move, and there is a successful *attack* landing on the piece’s square.

### Builds

Powers may build on any home center that they own. Home centers are the ones on the first two ranks on their side of the board: ranks `1` and `2` for England and Italy, and ranks `7` and `8` for France and Scandinavia. Some home centers can change ownership; this will be explained when pawns are introduced.

## Bishops and rooks: introducing multiple-square orders

Bishops and rooks move as they do in chess; their supports follow the same paths. These paths have a starting square, a landing square, and potential intermediate squares, these last squares being those between the starting and landing square, on the same rank, file, or diagonal.

### Multiple-square orders

A multiple-square order automatically issues a **convoy** order on each of its intermediate squares: such an order looks like

> `e2 C f1 - c4` or  
> `e2 C f1 S c4`,

where in the second example `c4` is the *landing square* of the support order from `f1`. Note that convoys are ordered to squares, not pieces. Also note that a square may receive multiple convoy orders. Powers may not explicitly order such moves, but they may support them with a new type of support, the **support-convoy**. Such an order looks like

> `Ke1 S e2 C f1 - c4`.

The prevent strength of a convoy order is the number of successful support-convoys that it receives. A convoy order fails if a move order onto its square succeeds, taking into account the convoy order's prevent strength. A convoy order also fails if its prevent strength is less than that of another convoy order on the same square. 

When adjudicating, multiple-square orders are treated like standard orders at their landing squares. Thus they can bounce, dislodge, etc.

### Castling

There is one exception to these multiple-square orders: castling. Castling is only allowed for a king and rook on the first rank on the power’s side, with the king on the square where the power originally had a king (file `d` or `e`), and the rook in the corner. For England and Scandinavia, the moves are mirrored to what they would be on a standard chess board (ie king’s side and queen’s side castling are flipped). The two pieces must also have not successfully moved before: for instance, one may castle right after building a king and a rook. The king’s move has no intermediate square but the rook move does: the squares between its starting and landing squares except for the one where the king lands. Castling pieces have attack and defend strength 0, but succeed against empty squares. In other words, they cannot dislodge a piece: this is an example of a travel order, a new type of order that will be detailed in the pawn section. Castling is ordered with a special order:

> `O-O` or `O-O-O`,

corresponding to castling where the rook moves two or three squares, respectively. A castling order succeeds when both travel orders succeed.

## Pawns: all the exceptions

Pawns travel forwards but attack diagonally. When on the first two ranks of their side, they can also advance two blocks, with an intermediate square: this rule is taken from horde chess.

### Travel and attack orders

This unique behavior means that pawn orders are more complicated than for other pieces. We introduce a distinction between two types of move orders: **travel** orders and **attack** orders. Attack orders are the usual orders, and unless otherwise specified, move orders are attack orders. Travel orders have 0 attack and defend strength on their own, but succeed against empty squares, and otherwise act like attack orders: they can be supported, bounced, etc.

Pawns may only be ordered to travel forwards and attack or support diagonally, except for en passant; see below. Travel orders are ordered like move orders, and with pawn orders we typically omit the piece name:

> `e2 - e4` is equivalent to `P e2 - e4`.

### Pawn attacks

An attacking pawn only moves if it successfully dislodges a piece. So a pawn attack can succeed, say by preventing another piece from landing on the attacked square, but the pawn itself will not move. This is also relevant when attacking multiple-square moves: pawns can tap the intermediate squares but will not move there.

### En passant

Pawns can also attack en passant, not only against pawns moving in the opposite direction, but also opponent pawns moving in the same direction. For en passant to be possible, the following conditions must hold:

- There must be a pawn that moves forwards two squares on the previous phase: call this the passed pawn.  
- An opponent pawn can currently attack the intermediate square of the two-square move.

For example, consider the following orders from the previous phase:

> `d7 - d5`  
> `e4 - e5`

In this case, the opponent pawn may receive an en passant order, which consists of an attack order on the passed pawn’s square and a travel order to the intermediate square. This is ordered as

> `e5 t d6 x d5`.

The attack and travel orders may be supported separately. For example, with the previous order.

> `Kc3 S e5 x d5`  
> `e7 S e5 t d6`

both support the en passant move. An en passant move succeeds when both the travel order and the attack order succeed. Note that a successful en passant order dislodges the passed pawn without actually occupying its square.

### Pawn promotion

Finally, a pawn that is on the back rank in the fall phase must be promoted to a knight, bishop, or rook in the build phase. Moreover, if the pawn is on a supply center, then this supply center becomes a home center of the pawn’s power. Build and disband syntax is the same as in standard Diplomacy.

# Dessert: an axiomatic approach

This axiomatic approach is inspired, and copies a lot of, the [DATC text](https://webdiplomacy.net/doc/DATC_v3_0.html). This section is somewhat incomplete, but any undefined terms should have been informally defined in the [previous section](#main-course-the-rules).

## Order syntax

Players write `<order>`s, which are converted into `<true order>`s during order validation. Order syntax is presented below in a sort of Backus-Naur form:

    <order> = <piece> <square> <action> | <castle order>
    <piece> = (empty) | P | N | B | R | K
    <square> = <file><rank>
    <file> = a | b | c | d | e | f | g | h
    <rank> = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8
    <action> = H | - <square> | S <square> <direct action> | t <square> x <square>
    <direct action> = H | - <square> | x <square> | t <square> | C <square> <convoy code> <square>
    <convoy code> = - | x | t | S
    <castle order> = O-O | O-O-O
     
    <true order> = <piece> <square> <true action>
    <true action> = <direct action> | S <square> <direct action>

The `(empty)` piece is used for convoy orders and when omitting the piece name for pawn orders.

## Special square names

Each power begins with a king. The square that this king begins on is called the power’s **king square**. The square on the same rank and in file `d` or `e` adjacent to this square is called the power’s **queen square**. The squares on the same rank are then named after the closer of these two squares and the non-pawn piece that begins there in standard chess: we get the **king/queen knight/bishop/rook squares**.

## Order validation

Consider an `<order>` submitted by a power.  
First consider the case where the order is `<piece> <square> <action>`.
- If `<piece>` is empty, then replace it with `P`.
- If the `<piece>` is not on `<square>` or does not belong to the power, then the order is invalidated.
- If `<action> == H`, then the order is validated.
- Otherwise, the order is of the form `<piece> <square0> . <square1> .*`.
    - If `<piece>` can move from `<square0>` to `<square1>` on an empty chess board, then the order is validated.
    - If the order is of the form `P <square0> t <square1> x <square2>`, the pawn could attack a piece on `<square1>`, another pawn passed `<square1>` to land on `<square2>` with a two-square move on the previous order phase, then the order is replaced by
        
        > `P<square0> t <square1>`  
        > `P<square0> x <square2>`,

        and these orders are validated.
    - Otherwise, if the order is of the form `P <square0> . <square1> .*` and the pawn could attack a piece on `<square1>`, then the order is validated.

Now consider the case where the order is `<castle order>`.
- If the order is `O-O`, there is a king on the power’s king square that has not moved yet, and there is a rook on the power’s king rook square that has not moved yet, then the order is replaced by

    > `K<king square> t <king knight square>`  
    > `R<king rook square> t <king bishop square>`,

    and these orders are validated.
- If the order is `O-O-O`, there is a king on the power’s king square that has not moved yet, and there is a rook on the power’s queen rook square that has not moved yet, then the order is replaced by

    > `K<king square> t <queen bishop square>`  
    > `R<king queen square> t <queen square>`,

    and these orders are validated.

In all other cases, the order is invalidated.

### Attack and travel orders

Powers order move orders. All move orders are attack orders EXCEPT for advancing pawns forwards and castling, which are travel orders.

### Implicit convoy orders

For bishop orders, rook orders, two-square pawn orders, and rook castling orders, there may be squares between the starting and landing square of the order on the same rank, file, or diagonal. These squares are called **intermediate squares** EXCEPT for the square where the castling king lands, for a rook castling order. If the order is `<piece> <square0> <convoy action code> <square1> .*` and `<square2>` is an intermediate square, then we add the order
    
> `<square 2> C <square0> <convoy action code> <square1>`.

## Dislodges

A piece is **dislodged** if it stays on its square and an attack order on its square succeeds.

Dislodged pieces are automatically disbanded.

## Path

All orders except for hold orders have a **path**.

The path of a move or support order is successful if there are no intermediate squares or if the convoy order of each intermediate square is successful. The path fails otherwise.  
The path of a convoy order is successful if all convoy orders for the same convoyed order that come before it are successful. The path fails otherwise.

## Head-to-head battle

A **head-to-head battle** is a pair of move orders from different powers where the starting square of one order is the landing square of the other, and vice-versa. Note that head-to-head battles cannot involve intermediate squares: due to the way pieces move, any such intermediate square would receive multiple convoy orders, making at least one of the two moves fail immediately.

## Strength computation

**Strength** is a number associated to a square or order:

- Squares have a [**hold** strength](#hold-strength).
- Attack and travel orders have an [**attack** strength](#attack-strength), a [**defend** strength](#defend-strength), and a [**prevent** strength](#prevent-strength).
- Convoy orders have a [**prevent** strength](#prevent-strength).

### Hold strength

The hold strength is 0 for a square that is empty, or that contains a unit that successfully vacates the square.  
It is 1 when the square contains a piece that has an unsuccessful move order.  
In all other cases, it is 1 plus the number of successful support-hold orders.

### Attack strength

If the [path](#path) of an *attack order* fails, then the attack strength of the attack order is 0\.  
Otherwise, if the landing square is empty, or if there is no [head-to-head battle](#head-to-head-battle) and the piece on the landing square successfully vacates the square, then the attack strength is 1 plus the number of successful support-move orders otherwise.  
Otherwise, if the piece on the landing square is of the same power, then the attack strength is 0\.  
Otherwise, the attack strength is 1 plus the number of successful support-move orders from pieces that are not of the same power as the piece on the landing square.

If the [path](#path) of a *travel order* fails, then the attack strength of the travel order is 0\.  
Otherwise, if the landing square is empty, or if there is no [head-to-head battle](#head-to-head-battle) and the piece on the landing square successfully vacates the square, then the attack strength is:

- ½ if there are no successful support-move orders (this is to allow traveling to empty squares);
- the number of successful support-move orders otherwise.

Otherwise, if the piece on the landing square is of the same power, then the attack strength is 0\.  
Otherwise, the attack strength is the number of successful support-move orders from pieces that are not of the same power as the piece on the landing square.

### Defend strength

If the [path](#path) of a move order fails, then the defend strength of the move order is 0\.  
The defend strength of an attack order is 1 plus the number of successful support-move orders.  
The defend strength of a travel order is the number of successful support-move orders\.

### Prevent strength

If the [path](#path) of a move order fails, then the prevent strength of the move order is 0\.  
If the move order is part of a [head-to-head battle](#head-to-head-battle) and the move order of the opposing piece is successful, then the prevent strength is 0\.  
Otherwise, the prevent strength is 1 plus the number of successful support-move orders.

If the [path](#path) of a convoy order fails, then the prevent strength of the convoy order is 0.  
Otherwise, its prevent strength is:

- ½ if there are no successful support-convoy orders (this is to allow the convoy to succeed over convoys with a failed path);
- the number of successful support-convoy orders otherwise.

## Order success
### Convoy orders

A convoy order succeeds if the following conditions are satisfied:

- The [path](#path) of the convoy order succeeds.
- No piece stays on its square or successfully attacks its square.
- Its prevent strength is greater than the prevent strength of any other convoy order on the same square.

Otherwise, it fails.

### Support orders

A support order fails when the piece is [dislodged](#dislodges-1), its [path](#path) fails, or when another piece is ordered to attack the square of the supporting piece and the following conditions are satisfied:

- The attacking piece is from a different power
- The landing square of the supported piece is not on the path of the piece attacking the support.
- The attacking piece’s path is successful.

Otherwise, it succeeds.

### Move orders

In case of a [head-to-head battle](#head-to-head-battle), a move order succeeds if its [attack strength](#attack-strength) is larger than the [defend strength](#defend-strength) of the opposing piece and larger than the [prevent strength](#prevent-strength) of any piece moving to the same square. Otherwise, it fails.

In case of no head-to-head battle, a move order succeeds if its [attack strength](#attack-strength) is larger than the [hold strength](#hold-strength) of the landing square and larger than the [prevent strength](#prevent-strength) of any piece moving to the same square. Otherwise, it fails.

### Exceptions

Coupled orders fail as soon as one of the two orders fails (for a reason other than the other order failing). This only applies to [castling](#castling) and [en passant](#en-passant) orders.

### Moving pieces

Pieces whose move order is successful are moved to the landing square of the move order (or travel order when different from the attack order).

### Paradoxes

A paradox is a set of orders with an ambiguous resolution, i.e. several or no solutions are possible. We adopt a standard way to address these:

- **Circular movement:** if a set of pieces each moves to the square of another piece, then these moves succeed.
- **Szykman rule:** if the paradox involves a convoy, the convoy fails.
