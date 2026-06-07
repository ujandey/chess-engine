# Chess Engine

A comprehensive Python chess engine with full legal move generation, sophisticated alpha-beta minimax search, Polyglot opening book support, UCI compatibility, SAN/PGN notation, extensive tests, benchmarks, and a Tkinter GUI.

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

Run benchmark/perft smoke tests:

```bash
py benchmark.py --perft-depth 3 --search-depth 5 --movetime 1.0
```

Run the UCI engine:

```bash
py -m engine.uci
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
|   |-- move_generator.py       # Move generation, search, evaluation, pruning
|   |-- opening_book.py         # Polyglot book loading and weighted move choice
|   |-- notation.py             # Standard Algebraic Notation & PGN
|   `-- uci.py                  # UCI protocol loop
|-- ui/
|   `-- gui.py                  # Tkinter board, eval bar, move history, time control
`-- tests/
    |-- test_castling.py
    |-- test_en_passant.py
    |-- test_game_state.py
    |-- test_pawn_promotion.py
    |-- test_notation_pgn_uci.py
    |-- test_state_integrity.py
    |-- test_gui_eval.py
    `-- ...
```

## Core Features

### Legal Move Generation
- **Complete rule support**: All standard chess rules including castling, en passant, promotion, check, checkmate, stalemate, 50-move rule, threefold repetition, and insufficient-material detection.
- **Optimized reverse-ray attack detection** (~10-20x faster than scanning all 64 squares) for efficient legality checking.
- **Cached king positions** (O(1) lookups) instead of O(64) board scans.
- **Piece position tracking** for fast iteration over only relevant pieces during move generation.

### Sophisticated Search Algorithm

The engine uses **iterative deepening with negamax search and principal variation search (PVS)** to find the best move:

#### Core Search Techniques
- **Negamax with alpha-beta pruning** - Efficient minimax variant reducing branching factor.
- **Principal Variation Search (PVS)** - Reduces branches searched by ~30-50% compared to vanilla alpha-beta.
- **Iterative deepening** - Reaches progressively deeper analysis depths while respecting time controls.
- **Transposition table** - Stores evaluated positions to avoid redundant computation. Default 64 MB (~224K entries).
- **Time-controlled search** - Respects time limits with tight polling (every 256 nodes for < 100ms moves).
- **Stop-flag support** - Can be interrupted gracefully mid-search, preserving board state.

#### Move Ordering & Heuristics
- **Transposition table move ordering (TT move)** - Prioritizes moves that previously proved best.
- **MVV-LVA capture ordering** (Most Valuable Victim - Least Valuable Attacker) - Capture ordering based on material exchange value.
- **Killer move heuristic** - Tracks moves that caused cutoffs at the same depth across sibling nodes.
- **History heuristic** - Weights quiet moves by their past success in cutoffs.
- **Check extension** - Extends search by 1 ply in positions where the side to move is in check.

#### Advanced Pruning Techniques
- **Null move pruning** - Assumes opponent can make a move and causes a cutoff; disabled in low-material endgames to avoid zugzwang blindness.
  - Material safety guard: requires ≥7 pawn units of non-pawn material to activate.
  - Reduction: 3 plies (conservative to avoid tactical losses).
- **Late move reductions (LMR)** - Assumes later moves are less likely to be best and reduces search depth:
  - Starts only after move index > 5 (preserves accuracy for top candidate moves).
  - Not applied to captures, promotions, or checking moves.
- **Quiescence search** - Extends search beyond nominal depth in positions with tactical threats (captures/checks):
  - Capture-only move generation to control branching.
  - Static exchange filtering (SEX) - Prunes clearly bad quiescence captures (losing > 0.2 pawn units).

#### Search Instrumentation
- **Selective depth tracking** - Monitors deepest ply reached within quiescence branches.
- **Node counting** - Tracks total nodes searched and nodes per second (NPS).
- **Depth reporting** - Prints depth-by-depth statistics during analysis.
- **Perft validation** - Built-in perft() and perft_divide() for move generation verification.

### Advanced Evaluation

Evaluation combines material and positional factors, with tapered transitions between middlegame and endgame phases:

#### Material & Basic PST
- **Piece values**: P=1, N=3, B=3, R=5, Q=9, K=0
- **Piece-square tables (PST)** - Encodes positional preferences for each piece type and board square.
  - Precomputed evaluation table (256 entries, one per square, each caching piece-value lookups) for O(64) board scan.
  - White perspective; black pieces mirror vertically.

#### Positional Factors
- **Bishop pair bonus** (+0.30) - Two bishops are worth more together than separately.
- **Pawn structure**:
  - Isolated pawn penalty (-0.20 per pawn) - Pawns with no adjacent friendly pawns.
  - Doubled pawn penalty (-0.15 per extra) - Multiple pawns on the same file.
- **Passed pawns** - Bonuses (0.10 to 0.65 pawn units) based on advancement rank (rank 1 start → rank 6 near promotion).
- **Rook file activity**:
  - Open file bonus (+0.20) - Rook on file with no pawns of either color.
  - Semi-open file bonus (+0.10) - Rook on file with no friendly pawns (but enemy pawns present).
- **Piece mobility** - Bonus for pieces with more legal move options:
  - Knight: 0.015 per move, Bishop: 0.012, Rook: 0.008, Queen: 0.004
- **King pressure** (middlegame only) - Bonus for attacking squares near the opponent's king:
  - Knight: 0.08, Bishop: 0.07, Rook: 0.10, Queen: 0.16
- **King safety** (middlegame-heavy) - Pawn shield bonuses and penalties for exposed files near the king:
  - Pawn shield bonus (+0.15 per shield pawn) - Pawns in front of the king.
  - Open/semi-open file penalties (-0.25/-0.15) for shield files with no friendly pawns.
- **Endgame king activity** - King centrality bonus (distance to center) scaled by endgame phase.

#### Game Phase Detection
- Linear tapered transition: phase fraction = (1.0 − (total_non_pawn_material − 10) / 50)
- 0.0 = full middlegame, 1.0 = pure endgame
- Prevents eval cliffs at phase transitions.

#### Terminal Position Scoring
- **Checkmate** - Scored as ±1000 +/- depth (prefers faster mates, delays losses).
- **Stalemate/draws** - Scored as 0 (50-move rule, threefold repetition, insufficient material).
- **Depth-aware mate scoring** - Stored in transposition table with ply offset to preserve mate-in-N accuracy.

### Board Representation

- **8x8 list of characters**: `K Q R B N P` (white), `k q r b n p` (black), `.` (empty)
- **Zobrist hashing** - 64-bit deterministic hashing with fixed seed for transposition table lookups and repetition detection:
  - 8 × 8 × 12 piece-square table (one hash per piece type on each square)
  - Side-to-move bit
  - 16 castling-right combinations
  - 8 en-passant file masks
- **Incrementally updated** in make_move() and undo_move() for O(1) hash updates.
- **Fully reversible moves** - make_move()/undo_move() restore all state (board, castling rights, en passant, halfmove clock, king caches, piece positions, Zobrist hash).
- **Cached king positions** (white_king_pos, black_king_pos) - O(1) king lookup instead of O(64) scan.
- **Piece position tracking** - Per-side sets of occupied squares for fast iteration.
- **Position counting** - Tracks position repetition for threefold repetition detection.

### Polyglot Opening Book Support

The engine uses the Titans Polyglot opening book for the opening phase:

- **Root-only usage**: Polyglot book lookup only at the start of find_best_move(); no book calls inside minimax search.
- **Lazy loading** - Opens and caches Titans.bin on first use.
- **Weighted randomness** - Selects among top-weighted book moves for variety.
- **Book exit condition** - Stops using book after 15 full moves (ply 30).
- **In-opening flag** - Once engine leaves book, it stays in search mode for this game.
- **Graceful fallback** - If book file or python-chess dependency is unavailable, cleanly falls back to minimax.
- **Safe FEN conversion** - Always uses halfmove_clock=0 and fullmove_number=1 for book lookups (Polyglot standard).

### Notation & PGN Export

- **Standard Algebraic Notation (SAN)** - Generates moves in chess notation (e.g., "e4", "Nf3+", "O-O").
- **PGN export** - Exports move history with variation branching and game metadata.
- **Move tree with variations** - Supports branching lines and navigation through alternative moves.

### UCI Protocol Support

- **Standard UCI commands**:
  - `position [fen <fen> | startpos] [moves <move1> ... <moveN>]` - Set board state.
  - `go [depth <d> | movetime <ms> | infinite]` - Search command with depth or time control.
  - `stop` - Stop search gracefully.
  - `setoption name Hash value <mb>` - Configure transposition table size.
  - `isready` - Confirm engine availability.
  - `quit` - Exit engine.
- **Info reporting** - Sends depth, score, nodes, NPS, hashfull, selective depth, and PV during search.
- **Mate score reporting** - Converts internal mate scores to UCI mate format (e.g., "mate 3").
- **Background search thread** - Non-blocking search with signal handling.

### GUI Features

Built with Tkinter for interactive play:

#### Core Gameplay
- **Visual board** - Unicode piece rendering with square highlighting.
- **Legal move highlighting** - Shows all legal destination squares when a piece is selected.
- **Move history panel** - Displays all moves in SAN notation with click-to-navigate support.
- **Evaluation bar** - Real-time visualization of position score (white advantage on top, black on bottom).
- **Best-move arrow** - Shows the engine's current best move.
- **Check highlighting** - Alerts the king square when in check.

#### Game Modes & Time Control
- **Human vs AI** - Play as white, black, or analyze.
- **Time controls** - Incremental (e.g., 5+0, 3+2) with clock display and ticking.
- **Search depth control** - Configurable search depth (default: 5) for fast/slow play.
- **Clock precision** - Millisecond-accurate timekeeping with visual countdown.

#### Navigation
- **Arrow keys** - Left/Right to navigate move history.
- **Click to jump** - Click any move in the history panel to jump to that position.
- **PGN export** - Copy game PGN to clipboard.

### Testing & Validation

**83 comprehensive tests** covering:

- **Castling** - Legality, move execution, undo restoration.
- **En passant** - Target setting, capture legality, pins, undo.
- **Pawn promotion** - Choice handling (Q/R/B/N), undo, capture promotion.
- **Terminal positions** - Checkmate, stalemate, 50-move rule, threefold repetition, insufficient material detection.
- **Board state integrity** - Zobrist hash restoration, piece position consistency, halfmove clock behavior.
- **GUI evaluation** - Score-to-ratio conversion, board snapshot restoration.
- **Notation & UCI** - SAN generation, PGN export, UCI move parsing, protocol compliance.
- **Perft validation** - Move generation correctness via perft bulky tests.

Run all tests:

```bash
py -m pytest
```

## Performance Characteristics

### Search Speed
- Typical search at depth 5: **1-3 seconds** on modern hardware (varies by position complexity).
- **Nodes per second (NPS)**: ~50K-200K depending on position branching and move ordering success.
- Time control support enables play at tournament time controls (classical, rapid, blitz).

### Memory Usage
- **Transposition table**: Default 64 MB (~224K entries, each ~300 bytes).
- **Zobrist hashing**: 64-bit deterministic for efficient position deduplication.
- **Configurable hash size** via `set_hash_size(mb)`.

### Move Generation
- **Perft benchmarks** validate move generation against known position counts.
- **Reverse-ray attack detection** for legality checking: ~10-20x faster than naive scanning.

## Configuration & Customization

### Search Depth
Adjust default GUI search depth in `ui/gui.py`:
```python
SEARCH_DEPTH = 5
```

### Hash Size
Configure transposition table size in UCI:
```
setoption name Hash value 128
```

Or programmatically:
```python
mg = MoveGenerator(board)
mg.set_hash_size(128)  # 128 MB
```

### Pruning Aggressiveness
Search depth thresholds and null-move reduction levels are in `engine/move_generator.py`:
- `depth >= 3` - Minimum depth for LMR and null move pruning.
- `move_index > 5` - LMR starts after the first 5 moves of a node.
- Null-move reduction: 3 plies (conservative for tactics).
- No null-move pruning in low-material endgames (material < 7 pawn units non-pawn).

## Current Limitations

- **Tkinter Unicode piece rendering** depends on local font support (may display as boxes on some systems).
- **Single-threaded search** - No parallel/multi-core search (SMP).
- **Limited opening preparation** - Relies on Polyglot book for opening (no learned openings).
- **No endgame tablebases** - No 7-piece tablebase support.
- **Evaluation simplicity** - No temporal dynamics, pawn-race calculations, or fortress detection.

## Future Improvements

- Parallel search (SMP) for multi-core systems.
- Endgame tablebase support (Syzygy format).
- Stronger evaluation with more positional nuance.
- Principal variation search refinements.
- Static exchange evaluation refinements.
- Opening book learning from engine games.

## Codebase Quality

Recent cleanup and verification:

- Removed tracked Python bytecode from version control.
- Added `.gitignore` for generated files.
- Full test suite passes (83 tests).
- All zobrist make/undo operations verified for correctness.
- Board state integrity preserved across search/undo cycles.

## References & Standards

- **UCI Protocol**: https://www.shogi.net/uci/
- **Polyglot Book Format**: https://www.chessprogramming.org/Polyglot
- **Standard Algebraic Notation (SAN)**: https://www.fide.com/rules (FIDE Laws of Chess)
- **Perft**: Position evaluation (move counting) for validation
- **Alpha-beta pruning**: https://www.chessprogramming.org/Alpha-Beta
- **Transposition tables**: https://www.chessprogramming.org/Transposition-Table
