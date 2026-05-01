import argparse
import time

from engine.board import Board
from engine.move_generator import MoveGenerator


POSITIONS = {
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "endgame": "8/2p5/3p4/3Pp3/2P1P3/6k1/8/6K1 w - - 0 1",
}


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


def main():
    parser = argparse.ArgumentParser(description="Chess engine benchmark suite")
    parser.add_argument("--perft-depth", type=int, default=3)
    parser.add_argument("--search-depth", type=int, default=5)
    parser.add_argument("--movetime", type=float, default=None, help="seconds per benchmark position")
    parser.add_argument("--skip-perft", action="store_true")
    parser.add_argument("--skip-search", action="store_true")
    args = parser.parse_args()

    if not args.skip_perft:
        run_perft(args.perft_depth)
    if not args.skip_search:
        run_search(args.search_depth, args.movetime)


if __name__ == "__main__":
    main()
