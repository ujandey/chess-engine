# Chess Engine

A Python chess engine with a Tkinter GUI, minimax search with alpha-beta pruning, a visual evaluation bar, move history with variation branching, PGN export, and full legal move generation for all special rules.

## Project Structure

```
chess-engine/
├── main.py                      # App entry point
├── engine/
│   ├── __init__.py
│   ├── board.py                 # Board state, reversible move execution
│   ├── move_generator.py        # Move generation, check detection, minimax search
│   └── notation.py              # Standard Algebraic Notation (SAN)
├── ui/
│   ├── __init__.py
│   └── gui.py                   # Tkinter GUI — board, eval bar, history panel
└── tests/
    ├── __init__.py
    ├── test_castling.py          # 16 castling tests
    ├── test_en_passant.py        # 9 en passant tests
    ├── test_pawn_promotion.py    # 11 promotion tests
    └── test_game_state.py        # 15 game state / evaluation tests
```

## How To Run

```bash
py main.py
```

Run the test suite:

```bash
py -m unittest discover -s tests
```

## Controls

| Action | How |
|---|---|
| Select a piece | Left-click it |
| Move | Click a highlighted destination square |
| Switch selection | Click another friendly piece |
| Navigate back | Left Arrow key |
| Navigate forward | Right Arrow key |
| Jump to any move | Click it in the history panel |
| Export PGN | Click **Copy PGN** button |

## Features

### Piece movement

Legal moves are generated for all six piece types: pawns, knights, bishops, rooks, queens, and kings.

### Legal move filtering

Every pseudo-legal move is simulated on the board, checked for self-check, and discarded if illegal. This is how pinned pieces and king safety are enforced — no special-case pin detection is needed.

### Check detection

`is_square_attacked` scans every enemy piece and asks whether it attacks the target square. Pawn attacks and king attacks use dedicated helpers (`get_pawn_attack_squares`, `get_king_attack_squares`) rather than movement generators, which is necessary for correct check detection and castling validation.

### Castling

Both kingside and queenside castling are supported for both sides. Castling is blocked when:

- the king is currently in check
- any square the king passes through or lands on is attacked
- the path between king and rook is occupied
- castling rights for that side have been lost

Castling rights are revoked when the king moves, when a rook moves from its starting square, or when a rook is captured on its starting square. All of this is fully reversible via `undo_move`.

### En passant

The board tracks `en_passant_target`, set only after a two-square pawn push. The move generator includes the en passant capture square in the pawn's pseudo-legal moves and it passes through legal move filtering like any other move — so en passant that would expose the king to check (the classic absolute-pin case) is correctly rejected.

### Pawn promotion

When a pawn reaches the last rank the GUI shows a modal dialog with four piece choices (queen, rook, bishop, knight). If the dialog is cancelled the move is not made. Promotion defaults to queen when no choice is provided (used internally by the engine).

### Endgame and draw detection

`get_game_status` checks for all five terminal conditions in priority order:

| Condition | Detection |
|---|---|
| Checkmate | King in check and no legal moves |
| Stalemate | King not in check and no legal moves |
| 50-move rule | `halfmove_clock >= 100` (auto-enforced) |
| Threefold repetition | `position_counts` keyed on `(board, turn, castling rights, en passant target)` |
| Insufficient material | K vs K, K+B vs K, K+N vs K, K+N vs K+N, K+B vs K+B (same square color) |

### Minimax engine with alpha-beta pruning

`find_best_move` searches to depth 3 by default. White maximizes, black minimizes. Alpha-beta pruning is applied at every node: the running best score from `find_best_move` is passed as the initial alpha/beta bound into `minimax`, so the first subtree prunes subsequent ones.

Piece values used in static evaluation:

| Piece | Value |
|---|---|
| Queen | 9 |
| Rook | 5 |
| Bishop | 3 |
| Knight | 3 |
| Pawn | 1 |

Mate scores are ±1000, depth-adjusted so the engine prefers faster mates.

### Evaluation bar

After every position change the engine runs a background search and renders the result as a vertical bar beside the board. The bar uses a `tanh`-based mapping so a small material advantage does not pin the bar to one extreme. The numeric score is displayed below the bar. Forced mate shows `+M` or `-M`.

### Best-move arrow

The engine's top candidate move is drawn as an arrow on the board — an orange highlight on the source square and an arrowhead pointing to the destination. The arrow disappears while a new search is running and is suppressed once the game is over.

### Background search with thread safety

Engine searches run in a daemon thread so the GUI stays responsive. The thread works on a fully independent `Board` copy created from a position snapshot, so it cannot interfere with the live board. Results are delivered to the main thread via `root.after(0, callback)`. A `_search_generation` counter ensures stale results from a superseded search are silently discarded.

### Move history panel

Every move is recorded in SAN (Standard Algebraic Notation) and displayed in a scrollable panel to the right of the eval bar. The panel uses a Tkinter `Text` widget with per-node click tags. Clicking any move in the panel jumps directly to that position. The current move is highlighted in amber.

### Standard Algebraic Notation

`engine/notation.py` generates correct SAN for every move type:

- **Piece prefix** — omitted for pawns, uppercase letter for all others
- **Disambiguation** — when two same-type same-color pieces can reach the same square, the moving piece's file is added; if that is not unique, the rank; if still not unique, both
- **Capture marker** — `x`, with pawn file prepended for pawn captures (including en passant)
- **Destination square** — algebraic square name
- **Promotion suffix** — `=Q`, `=R`, `=B`, or `=N`
- **Check / checkmate suffix** — `+` or `#`, determined by simulating the move, checking the result, then undoing

### Variation branching

Playing a move from a historical position creates a new branch rather than truncating the main line. Each move is stored as a `GameNode` in a tree. `record_move` checks whether the move already exists as a child of the current node — if so it navigates there without creating a duplicate. Variations are rendered inline in the history panel with parentheses and dimmed text, matching standard chess notation style.

### PGN export

The **Copy PGN** button builds a PGN string including standard headers (Event, Site, Date, White, Black, Result) and the full game tree with variations, then copies it to the clipboard. Move numbering is handled correctly across variation boundaries — after a white variation closes, the next black move gets a `N...` prefix.

## Architecture

### Board representation

`engine/board.py` stores the position as an 8×8 list of characters. Uppercase = white, lowercase = black, `.` = empty.

```
K Q R B N P   (white)
k q r b n p   (black)
.             (empty)
```

Board state fields: `board`, `turn`, `castling_rights`, `en_passant_target`, `halfmove_clock`, `position_counts`.

### Reversible move execution

`make_move(start, end, promotion_choice)` applies a move and returns a `move_state` dict capturing everything needed to undo it: the captured piece, en passant capture square and piece, previous castling rights, previous en passant target, previous halfmove clock, promotion piece, and rook move for castling. `undo_move(start, end, move_state)` fully restores the board from that dict.

`move_piece` wraps `make_move`, flips `turn`, and calls `record_current_position`. It is used only for real played moves; `make_move` / `undo_move` are used internally by move generation and the engine.

### Game tree

```python
class GameNode:
    id         # unique integer
    position   # board snapshot dict (deep copy of all board state)
    move       # (start, end, promo_choice) tuple, or None for root
    move_san   # SAN string, e.g. "Nf3", "O-O", "exd5+"
    parent     # parent GameNode, or None
    children   # list of GameNode — children[0] is the main line
```

The GUI keeps a `_node_by_id` dict for O(1) lookup when a history click arrives. Navigating to any node restores that snapshot via `_restore`, which deep-copies all board state including `position_counts`.

### Move generation flow

1. `get_piece_moves` dispatches to the piece-specific generator.
2. Piece generators produce pseudo-legal moves (no self-check filtering).
3. `get_legal_moves` simulates each pseudo-legal move, calls `is_in_check`, and keeps only safe moves.
4. `generate_all_legal_moves` iterates the board and collects `(start, end)` pairs for all pieces of one side — used by the engine and `has_any_legal_moves`.
5. `is_square_attacked` is used by check detection and castling validation.
6. `get_game_status` is called after every move to update the status bar and stop the game.

## Tests

51 tests across 4 files, run with `py -m unittest discover -s tests`.

**`test_castling.py` — 16 tests**
- White and black kingside and queenside castling legality
- Rook placement after castling and full undo verification
- Cannot castle when in check
- Cannot castle kingside or queenside through an attacked square
- Cannot castle when the path is occupied
- Castling rights revoked after king moves, after kingside rook moves, after queenside rook moves — all with undo verification

**`test_en_passant.py` — 9 tests**
- En passant target set correctly after white and black two-square pawn pushes
- En passant target cleared after any other move
- White captures en passant left and right, with undo restoring the captured pawn
- Black captures en passant right and left, with undo restoring the captured pawn
- En passant not available when target is not set
- En passant filtered when it would leave the king in check (absolute rank pin)

**`test_pawn_promotion.py` — 11 tests**
- White and black promotion to all four pieces (queen, rook, bishop, knight) with undo
- White and black promotion via diagonal capture with undo
- Invalid promotion choice defaults to queen

**`test_game_state.py` — 15 tests**
- Static evaluation: equal material, extra queen, material from black's perspective
- Checkmate evaluation: correct sign, depth-aware score
- Checkmate and stalemate detection via `get_game_status`
- Insufficient material: king vs king, knight vs knight, same-color bishops
- 50-move rule detection
- Threefold repetition detection via repeated knight moves
- Halfmove clock: resets on pawn move, increments on quiet move, restored on undo

## Current Limitations

- No AI opponent in the GUI — the engine evaluates positions and shows the best move arrow, but does not play moves automatically
- No game clocks or time controls
- Unicode chess piece symbols may render oddly on some systems depending on font availability
