# Chess Dip: a Diplomacy variant on a chess board

This Diplomacy variant was created for the DiploStrats Diplomacy variant
design contest. This repository contains a `Python` implementation of
the variant, using `matplotlib` as a renderer. This a work in progress.

![A spring 01 phase](/docs/images/r2.png)

## Variant rules

Read `RULES.md` for the rules.

## How to run the program

The file `sample.py` has two functions for you to try: `sandbox()` and
`test_cases()`. `sandbox()` will setup the board and open a console
interface for you to input orders. `test_cases()` opens an console
interface where you can run various DATC-inspired tests. In either case,
typing `help` will give a list of possible instructions.

## How to run a game

There is currently no automated way to run a game of Chess Dip. My
recommendation is to have a GM that inputs orders via the sandbox mode,
sharing renders of the board to the players. The sandbox can validate
moves, adjudicate, and keep track of phases, but the GM will have to
keep track of the adjustment phase (builds, piece promotion).