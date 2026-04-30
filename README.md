# Chess Engine

A Python chess engine with a Tkinter GUI, full legal move generation, SAN/PGN support, a Polyglot opening book, and an alpha-beta search tuned with common engine pruning techniques.

## Quick Start

Install dependencies:

```bash
py -m pip install -r requirements.txt
```

Run the GUI:

```bash
py main.py
```

Run tests:

```bash
py -m pytest
```

## Project Structure

```text
chess-engine/
|-- main.py
|-- requirements.txt
|-- Titans/
|   `-- Titans.bin              # Polyglot opening book
|-- engine/
|   |-- board.py                # Board state, FEN, Zobrist hash, reversible moves
|   |-- move_generator.py       # Move generation, search, pruning, evaluation
|   |-- opening_book.py         # Polyglot book loading and weighted move choice
|   `-- notation.py             # Standard Algebraic Notation
|-- ui/
|   `-- gui.py                  # Tkinter board, eval bar, move history
`-- tests/
    |-- test_castling.py
    |-- test_en_passant.py
    |-- test_game_state.py
    `-- test_pawn_promotion.py
```

## Current Engine Features

- Legal move generation for all standard chess moves.
- Castling, en passant, promotion, check, checkmate, stalemate, 50-move rule, threefold repetition, and insufficient-material detection.
- Standard Algebraic Notation generation and PGN export.
- Move-history tree with variation branching.
- Background engine search so the GUI stays responsive.
- Best-move arrow and evaluation bar.
- Polyglot opening book support via `Titans/Titans.bin`.
- Search depth is currently `5` in the GUI.

## Opening Book

The engine uses `python-chess` only at the root of `find_best_move()` for Polyglot book lookup. No FEN conversion or `python-chess` calls happen inside minimax.

Book behavior:

- Loads `Titans/Titans.bin` lazily and only once.
- Converts the custom board to FEN with book-safe counters: `halfmove_clock=0`, `fullmove_number=1`.
- Selects among the top weighted book entries using weighted randomness.
- Stops using book moves after 15 full moves.
- Maintains an `in_opening` flag so once the engine leaves book, it stays in search mode.
- Falls back cleanly to minimax if the book file or dependency is unavailable.

## Board Representation

The board is an 8x8 list of piece characters:

```text
K Q R B N P   white
k q r b n p   black
.             empty
```

Important board state:

- `board`
- `turn`
- `castling_rights`
- `en_passant_target`
- `halfmove_clock`
- `position_counts`
- `white_king_pos`
- `black_king_pos`
- Zobrist piece hash

`make_move()` and `undo_move()` are fully reversible and restore board contents, castling rights, en passant target, halfmove clock, king caches, and Zobrist hash.

## Zobrist Hashing

`engine/board.py` uses deterministic 64-bit Zobrist hashing with a fixed seed for reproducibility.

Hash components:

- 8 x 8 x 12 piece-square table
- side to move
- 16 castling-right states
- 8 en-passant files

The piece hash is updated incrementally in `make_move()` for:

- normal moves
- captures
- en passant captures
- promotions
- castling rook movement

`undo_move()` restores the previous piece hash exactly. The final `zobrist_hash` property dynamically includes side, castling, and en passant so existing direct turn assignments in the search and tests remain safe.

## Search

The engine uses iterative deepening at the root, alpha-beta minimax, transposition table lookup, quiescence search, and move ordering.

Search instrumentation prints:

```text
Nodes: X
Time: Y seconds
NPS: Z
```

Search optimizations:

- Transposition table keyed by `board.zobrist_hash`.
- TT entries store depth, value, flag, and best move.
- TT move ordering.
- MVV-LVA-style capture ordering.
- Killer move heuristic.
- History heuristic.
- Quiescence search with capture-only move generation.
- Null move pruning with a material safety guard.
- Late move reductions with a conservative safety threshold.
- Check extensions: positions where the side to move is in check search one ply deeper.
- Cached king positions and reverse-ray attack detection.
- Precomputed evaluation table for fast material and piece-square scoring.

## Pruning Safety Layer

The search deliberately avoids the most aggressive versions of pruning:

- Null move pruning is disabled in low-material endgames.
- LMR starts only after move index `> 5`.
- LMR is not applied to captures, promotions, or checking moves.
- Check extensions reduce tactical blindness in forcing lines.

This keeps depth 5 practical while preserving more tactical reliability than a maximum-speed pruning setup.

## Evaluation

Evaluation is material plus piece-square tables from White's perspective. Public `evaluate_position(depth=0)` remains terminal-aware so checkmates and draws are scored correctly, while `_evaluate_material()` is used in hot search paths.

Mate scores are depth-adjusted around `+/-1000`, so the engine prefers faster mates and delays losing ones.

## GUI Controls

| Action | How |
|---|---|
| Select a piece | Left-click it |
| Move | Click a highlighted destination |
| Switch selection | Click another friendly piece |
| Navigate back | Left Arrow |
| Navigate forward | Right Arrow |
| Jump to move | Click a move in the history panel |
| Export PGN | Click Copy PGN |

## Codebase Audit Notes

Recent audit and cleanup:

- Removed tracked Python bytecode from version control.
- Added `.gitignore` for generated Python/cache files.
- Added `requirements.txt` for the `python-chess` dependency.
- Verified the opening book is root-only and does not enter minimax.
- Verified Zobrist make/undo restoration for normal moves and promotions.
- Verified the full test suite passes.

## Tests

Current suite: 51 tests.

Coverage areas:

- Castling legality and undo
- En passant legality, pins, and undo
- Promotion choices and undo
- Checkmate and stalemate detection
- 50-move rule
- Threefold repetition
- Insufficient material
- Evaluation sign and mate-depth behavior
- Halfmove clock behavior

Run:

```bash
py -m pytest
```

## Current Limitations

- The GUI shows the engine's best move but does not automatically play engine moves.
- No clocks or time controls.
- Tkinter Unicode piece rendering depends on local font support.
