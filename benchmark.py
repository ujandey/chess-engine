import argparse
import time

from engine.board import Board
from engine.move_generator import MoveGenerator
from engine.uci import move_to_uci


POSITIONS = {
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "endgame": "8/2p5/3p4/3Pp3/2P1P3/6k1/8/6K1 w - - 0 1",
}

TACTICAL_POSITIONS = [
    {
        "name": "back_rank_mate_in_1",
        "fen": "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
        "best": {"a1a8"},
        "depth": 1,
    },
    {
        "name": "queen_mate_in_1",
        "fen": "k7/8/KQ6/8/8/8/8/8 w - - 0 1",
        "best": {"b6a7", "b6b7", "b6b8"},
        "depth": 1,
    },
    {
        "name": "rook_king_support_mate_in_1",
        "fen": "7k/5K2/6R1/8/8/8/8/8 w - - 0 1",
        "best": {"g6h6"},
        "depth": 1,
    },
    {
        "name": "knight_fork_wins_rook",
        "fen": "8/3r4/2k5/8/8/5N2/8/R3K3 w - - 0 1",
        "best": {"f3e5"},
        "depth": 3,
    },
    {
        "name": "bishop_captures_pinned_knight",
        "fen": "8/8/4k3/8/2n5/8/B7/4K3 w - - 0 1",
        "best": {"a2c4"},
        "depth": 1,
    },
    {
        "name": "rook_capture_back_rank_mate",
        "fen": "r5k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
        "best": {"a1a8"},
        "depth": 1,
    },
    {
        "name": "pawn_promotes_to_queen",
        "fen": "8/6P1/6K1/8/8/8/8/7k w - - 0 1",
        "best": {"g7g8q"},
        "depth": 1,
    },
]


def run_perft(depth):
    for name, fen in POSITIONS.items():
        board = Board()
        board.set_fen(fen)
        mg = MoveGenerator(board)
        started = time.perf_counter()
        nodes = mg.perft(depth)
        elapsed = time.perf_counter() - started
        nps = int(nodes / elapsed) if elapsed > 0 else 0
        print(f"perft {name:8s} depth={depth} nodes={nodes:,} time={elapsed:.3f}s nps={nps:,}")


def run_search(depth, movetime):
    for name, fen in POSITIONS.items():
        board = Board()
        board.set_fen(fen)
        mg = MoveGenerator(board)
        started = time.perf_counter()
        move, score = mg.find_best_move(depth, board.turn == "white", max_time=movetime, verbose=False)
        elapsed = time.perf_counter() - started
        nps = int(mg.node_count / elapsed) if elapsed > 0 else 0
        print(
            f"search {name:8s} depth={mg.last_completed_depth}/{depth} "
            f"move={move} score={score:.3f} nodes={mg.node_count:,} "
            f"time={elapsed:.3f}s nps={nps:,}"
        )


def run_tactics(depth_override=None, movetime=None):
    solved = 0
    for tactic in TACTICAL_POSITIONS:
        board = Board()
        board.set_fen(tactic["fen"])
        mg = MoveGenerator(board)
        mg.in_opening = False
        depth = depth_override if depth_override is not None else tactic["depth"]
        started = time.perf_counter()
        move, score = mg.find_best_move(depth, board.turn == "white", max_time=movetime, verbose=False)
        elapsed = time.perf_counter() - started
        found = move_to_uci(move) if move else "none"
        ok = found in tactic["best"]
        solved += int(ok)
        nps = int(mg.node_count / elapsed) if elapsed > 0 else 0
        status = "ok" if ok else "miss"
        print(
            f"tactic {tactic['name']:32s} depth={mg.last_completed_depth}/{depth} "
            f"move={found:6s} expected={','.join(sorted(tactic['best'])):17s} "
            f"status={status:4s} score={score:.3f} nodes={mg.node_count:,} "
            f"time={elapsed:.3f}s nps={nps:,}"
        )
    print(f"tactic solved {solved}/{len(TACTICAL_POSITIONS)}")


def main():
    parser = argparse.ArgumentParser(description="Chess engine benchmark suite")
    parser.add_argument("--perft-depth", type=int, default=3)
    parser.add_argument("--search-depth", type=int, default=5)
    parser.add_argument("--movetime", type=float, default=None, help="seconds per benchmark position")
    parser.add_argument("--tactics-depth", type=int, default=None, help="override per-position tactical search depth")
    parser.add_argument("--skip-perft", action="store_true")
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--skip-tactics", action="store_true")
    args = parser.parse_args()

    if not args.skip_perft:
        run_perft(args.perft_depth)
    if not args.skip_search:
        run_search(args.search_depth, args.movetime)
    if not args.skip_tactics:
        run_tactics(args.tactics_depth, args.movetime)


if __name__ == "__main__":
    main()
