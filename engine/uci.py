import sys
import time

from engine.board import Board
from engine.move_generator import MoveGenerator


STARTPOS_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_VALID_PROMOS = frozenset("QRBN")

_OPTIONS = {
    "Hash":          ("spin", 64,  1,    2048),  # (type, default, min, max)
    "Move Overhead": ("spin", 50,  0,    5000),
    "Threads":       ("spin",  1,  1,       1),
}


def square_to_coord(square):
    row, col = square
    return f"{chr(ord('a') + col)}{8 - row}"


def coord_to_square(text):
    return 8 - int(text[1]), ord(text[0]) - ord("a")


def move_to_uci(move):
    if move is None:
        return "0000"
    start, end = move[0], move[1]
    promo = move[2] if len(move) > 2 else None
    result = square_to_coord(start) + square_to_coord(end)
    if promo is not None:
        result += promo.lower()
    return result


def apply_uci_move(board, mg, move_text):
    start = coord_to_square(move_text[:2])
    end = coord_to_square(move_text[2:4])
    promotion = move_text[4].upper() if len(move_text) > 4 else None

    if promotion is not None and promotion not in _VALID_PROMOS:
        print(f"info string illegal move ignored: {move_text}", flush=True)
        return

    if mg is not None:
        is_white = board.turn == "white"
        legal_moves = mg.generate_all_legal_moves(is_white)
        legal_endpoints = {(s, e) for s, e, _ in legal_moves}
        if (start, end) not in legal_endpoints:
            print(f"info string illegal move ignored: {move_text}", flush=True)
            return

    board.make_move(start, end, promotion)
    board.turn = "black" if board.turn == "white" else "white"
    board.record_current_position()


def configure_position(board, mg, args):
    if not args:
        return

    if args[0] == "startpos":
        board.set_fen(STARTPOS_FEN)
        move_index = 1
    elif args[0] == "fen":
        if "moves" in args:
            move_index = args.index("moves")
            fen = " ".join(args[1:move_index])
        else:
            move_index = len(args)
            fen = " ".join(args[1:])
        board.set_fen(fen)
    else:
        return

    mg.in_opening = True
    if move_index < len(args) and args[move_index] == "moves":
        for move_text in args[move_index + 1:]:
            apply_uci_move(board, mg, move_text)
        mg.in_opening = False


def _compute_movetime(args, is_white):
    """Return search time in seconds from go parameters, or None if not applicable."""
    def get_int(key, default=None):
        if key in args:
            idx = args.index(key)
            if idx + 1 < len(args):
                try:
                    return int(args[idx + 1])
                except ValueError:
                    pass
        return default

    wtime = get_int("wtime")
    btime = get_int("btime")
    winc  = get_int("winc",  0)
    binc  = get_int("binc",  0)
    movestogo = get_int("movestogo")
    overhead_ms = get_int("Move Overhead", _OPTIONS["Move Overhead"][1])

    time_left_ms = (wtime if is_white else btime)
    inc_ms       = (winc  if is_white else binc)

    if time_left_ms is None:
        return None

    if movestogo and movestogo > 0:
        allotted_ms = time_left_ms / movestogo + inc_ms
    else:
        allotted_ms = time_left_ms / 40 + inc_ms * 0.8

    # Never use more than half the remaining clock
    allotted_ms = min(allotted_ms, time_left_ms / 2)
    allotted_ms -= overhead_ms
    return max(0.05, allotted_ms / 1000.0)


def parse_go(args, is_white):
    depth = 64
    movetime = None

    if "infinite" in args:
        return depth, None

    if "depth" in args:
        idx = args.index("depth")
        if idx + 1 < len(args):
            depth = int(args[idx + 1])

    if "movetime" in args:
        idx = args.index("movetime")
        if idx + 1 < len(args):
            movetime = max(0.01, int(args[idx + 1]) / 1000.0)

    if movetime is None:
        movetime = _compute_movetime(args, is_white)

    return depth, movetime


def _format_score(score_pawns):
    """Return UCI score string: 'cp X' or 'mate N'."""
    mate_threshold = MoveGenerator.MATE_SCORE - 50
    if abs(score_pawns) >= mate_threshold:
        plies = MoveGenerator.MATE_SCORE - int(abs(score_pawns))
        n = max(1, (plies + 1) // 2)
        return f"mate {n if score_pawns > 0 else -n}"
    return f"cp {int(score_pawns * 100)}"


def make_info_callback(mg, t0):
    def callback(depth, score, pv):
        elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
        nps = int(mg.node_count / (elapsed_ms / 1000.0))
        pv_str = " ".join(move_to_uci(m) for m in pv)
        score_str = _format_score(score)
        seldepth = max(depth, mg.seldepth)
        hashfull = (
            min(1000, int(len(mg.transposition_table) * 1000 / mg.tt_max_entries))
            if mg.tt_max_entries else 0
        )
        line = (f"info depth {depth} seldepth {seldepth} score {score_str}"
                f" nodes {mg.node_count} nps {nps} hashfull {hashfull} time {elapsed_ms}")
        if pv_str:
            line += f" pv {pv_str}"
        print(line, flush=True)
    return callback


def main():
    board = Board()
    mg = MoveGenerator(board)

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        command = parts[0]
        args = parts[1:]

        if command == "uci":
            print("id name Suar")
            print("id author Ujan Dey")
            for name, (opt_type, default, mn, mx) in _OPTIONS.items():
                print(f"option name {name} type {opt_type} default {default} min {mn} max {mx}")
            print("uciok")

        elif command == "setoption":
            # setoption name <Name> value <val>
            if "name" in args:
                name_idx = args.index("name")
                if "value" in args:
                    val_idx = args.index("value")
                    opt_name = " ".join(args[name_idx + 1:val_idx])
                    val_str  = " ".join(args[val_idx + 1:])
                else:
                    opt_name = " ".join(args[name_idx + 1:])
                    val_str  = None

                if opt_name == "Hash" and val_str is not None:
                    try:
                        mg.set_hash_size(int(val_str))
                    except ValueError:
                        pass
                elif opt_name == "Move Overhead" and val_str is not None:
                    try:
                        _OPTIONS["Move Overhead"] = (_OPTIONS["Move Overhead"][0],
                                                     int(val_str),
                                                     *_OPTIONS["Move Overhead"][2:])
                    except ValueError:
                        pass
                # Threads: always 1, silently accepted

        elif command == "isready":
            print("readyok")

        elif command == "ucinewgame":
            board = Board()
            mg = MoveGenerator(board)

        elif command == "position":
            configure_position(board, mg, args)

        elif command == "go":
            is_white = board.turn == "white"
            depth, movetime = parse_go(args, is_white)
            t0 = time.perf_counter()
            callback = make_info_callback(mg, t0)
            best_move, score = mg.find_best_move(
                depth, is_white, max_time=movetime, verbose=False,
                on_depth_complete=callback,
            )
            # Opening book or sub-depth-1 timeout: emit a minimal info line
            if mg.last_completed_depth == 0 and best_move is not None:
                elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
                pv_str = move_to_uci(best_move)
                # score from find_best_move is white-perspective; flip to side-to-move perspective
                mover_score = score if is_white else -score
                print(f"info depth 1 seldepth 1 score {_format_score(mover_score)}"
                      f" nodes {mg.node_count} nps 0 time {elapsed_ms} pv {pv_str}", flush=True)
            print(f"bestmove {move_to_uci(best_move)}", flush=True)

        elif command == "stop":
            mg.stop_search = True

        elif command == "quit":
            break

        sys.stdout.flush()


if __name__ == "__main__":
    main()
