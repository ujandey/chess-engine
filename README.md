# Chess Engine

A small Python chess project with:

- a basic chess engine
- a Tkinter GUI
- legal move filtering
- support for core special rules like castling, en passant, and promotion

The project is currently focused on move generation and playable local interaction rather than AI search.

## Project Structure

- [main.py](c:/Users/ANUSKA/Desktop/chess-engine/main.py): app entry point
- [engine/board.py](c:/Users/ANUSKA/Desktop/chess-engine/engine/board.py): board state, reversible move execution, castling/en passant/promotion state
- [engine/move_generator.py](c:/Users/ANUSKA/Desktop/chess-engine/engine/move_generator.py): piece move generation, attack detection, check detection, legal move filtering
- [ui/gui.py](c:/Users/ANUSKA/Desktop/chess-engine/ui/gui.py): Tkinter chessboard and player interaction
- [tests/test_castling.py](c:/Users/ANUSKA/Desktop/chess-engine/tests/test_castling.py): castling tests
- [tests/test_pawn_promotion.py](c:/Users/ANUSKA/Desktop/chess-engine/tests/test_pawn_promotion.py): promotion tests

## Features Implemented

### Piece movement

The engine currently generates moves for:

- pawns
- knights
- bishops
- rooks
- queens
- kings

### Legal move filtering

The engine does not just generate raw piece moves. It also filters them into legal moves.

How it works:

1. Generate pseudo-legal moves for the selected piece.
2. Temporarily simulate each move on the board.
3. Check whether that move leaves the moving side's king in check.
4. Keep only the moves that are safe.

This logic lives mainly in [engine/move_generator.py](c:/Users/ANUSKA/Desktop/chess-engine/engine/move_generator.py:242) and uses reversible move helpers in [engine/board.py](c:/Users/ANUSKA/Desktop/chess-engine/engine/board.py:35).

### Check detection

The engine can:

- find the white or black king
- determine whether a square is attacked
- determine whether a side is in check

Important detail:

- pawn attack squares are handled separately from pawn forward movement
- king attack squares are handled separately from king movement

That separation is necessary for correct check detection and castling validation.

### Castling

Both castling directions are supported:

- kingside castling
- queenside castling

The engine tracks castling rights in the board state and updates them when:

- a king moves
- a rook moves
- a rook is captured on its original square

Castling is allowed only when:

- the king is not already in check
- the path squares are empty
- the king does not move through an attacked square
- the destination square is not attacked
- the corresponding rook is still present
- castling rights are still available

When castling is executed, the rook is moved automatically.

### En passant

En passant is supported.

The board tracks `en_passant_target`, which is set only after a pawn makes a two-square move.

The engine:

- adds the en passant capture square to pawn legal moves when valid
- removes the captured pawn during execution
- restores the captured pawn during undo

This is important because legal move filtering relies on temporary move simulation.

### Pawn promotion

Pawn promotion is supported.

Engine behavior:

- if a pawn reaches the last rank, it is promoted
- if no promotion choice is provided, promotion defaults to queen
- undo restores the original pawn correctly

GUI behavior:

- when a real player move reaches the last rank, the GUI asks for `Q`, `R`, `B`, or `N`
- if the dialog is canceled, the move is not made

## GUI Features

The GUI is implemented in [ui/gui.py](c:/Users/ANUSKA/Desktop/chess-engine/ui/gui.py:1) using Tkinter.

Current behavior:

- click a piece to select it
- the selected square is highlighted
- legal destination squares are outlined
- only the side whose turn it is can be selected
- if a king is in check, its square is highlighted in red
- if the user tries a pseudo-legal move that is actually illegal because it exposes the king, the king square is highlighted in red

This helps show pinned-piece situations and self-check attempts visually.

## How To Run

### Start the GUI

Run:

```bash
py main.py
```

This opens the Tkinter chess window.

### Controls

- click once to select a piece
- click a highlighted legal destination to move
- click another piece of the same side to switch selection
- if a pawn reaches the last rank, enter `Q`, `R`, `B`, or `N` in the promotion prompt

## How The Engine Works

### Board state

[engine/board.py](c:/Users/ANUSKA/Desktop/chess-engine/engine/board.py:1) stores:

- `board`: the 8x8 grid
- `turn`: whose turn it is
- `castling_rights`: available castling options
- `en_passant_target`: the square available for en passant capture

### Reversible move execution

The board uses reversible move helpers so the engine can test moves safely:

- `make_move(...)`
- `undo_move(...)`

These methods handle:

- normal captures
- en passant captures
- castling rook movement
- promotion
- restoration of castling rights
- restoration of en passant state

### Move generation flow

[engine/move_generator.py](c:/Users/ANUSKA/Desktop/chess-engine/engine/move_generator.py:1) follows this general flow:

1. `get_piece_moves(...)` dispatches to the correct generator for the piece.
2. Piece-specific generators produce pseudo-legal moves.
3. `get_legal_moves(...)` simulates each move and removes illegal ones.
4. `is_square_attacked(...)` is used for check and castling rules.
5. `is_in_check(...)` uses attack detection on the king square.

## Tests

Current automated tests cover:

- queenside castling legality
- queenside rook movement during castling
- undo after castling
- white default queen promotion
- black default queen promotion
- white custom knight promotion
- black custom rook promotion
- undo after promotion

Run the tests with:

```bash
py -m unittest tests\test_castling.py tests\test_pawn_promotion.py
```

If you want a syntax-only check without writing `.pyc` files:

```bash
$env:PYTHONDONTWRITEBYTECODE='1'; py -m py_compile main.py engine\board.py engine\move_generator.py ui\gui.py tests\test_castling.py tests\test_pawn_promotion.py
```

## Current Limitations

The project is playable, but it is not a full production chess engine yet.

Things not clearly implemented yet:

- checkmate detection
- stalemate detection
- draw rules such as threefold repetition
- fifty-move rule
- insufficient material detection
- move history / PGN / notation export
- AI opponent or search
- timers / clocks
- polished promotion popup UI
- robust test coverage for every piece and edge case

Also note:

- the GUI piece symbols may render oddly on some systems because the current Unicode strings in [ui/gui.py](c:/Users/ANUSKA/Desktop/chess-engine/ui/gui.py:5) look mojibaked and may need cleanup

## Suggested Next Steps

Good next improvements would be:

- add checkmate and stalemate detection
- add tests for en passant and pinned pieces
- replace the text-based promotion prompt with a clickable popup
- fix the Unicode chess symbols in the GUI
- add move history display
- add an AI player

## Summary

This project now supports the main move rules needed for a functional local chess game:

- legal move generation
- check detection
- kingside and queenside castling
- en passant
- pawn promotion with choice in the GUI
- move highlighting and check highlighting in the board UI

It is a solid base to keep building on.
