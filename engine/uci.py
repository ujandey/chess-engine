import sys
import threading
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


def _is_coord(text):
    return len(text) == 2 and text[0] in "abcdefgh" and text[1] in "12345678"


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
    if len(move_text) not in (4, 5) or not _is_coord(move_text[:2]) or not _is_coord(move_text[2:4]):
        print(f"info string illegal move ignored: {move_text}", flush=True)
        return False

    start = coord_to_square(move_text[:2])
    end = coord_to_square(move_text[2:4])
    promotion = move_text[4].upper() if len(move_text) > 4 else None

    if promotion is not None and promotion not in _VALID_PROMOS:
        print(f"info string illegal move ignored: {move_text}", flush=True)
        return False

    if mg is not None:
        is_white = board.turn == "white"
        legal_moves = mg.generate_all_legal_moves(is_white)
        if (start, end, promotion) not in legal_moves:
            print(f"info string illegal move ignored: {move_text}", flush=True)
            return False

    board.make_move(start, end, promotion)
    board.turn = "black" if board.turn == "white" else "white"
    board.record_current_position()
    return True


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


def make_info_callback(mg, t0, emit=None):
    if emit is None:
        emit = lambda line: print(line, flush=True)

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
        emit(line)
    return callback


class UciEngine:
    def __init__(self, emit=None):
        self.board = Board()
        self.mg = MoveGenerator(self.board)
        self.search_thread = None
        self._emit = emit or self._print

    @staticmethod
    def _print(line):
        print(line, flush=True)

    def _search_is_active(self):
        return self.search_thread is not None and self.search_thread.is_alive()

    def stop_search(self):
        if self._search_is_active():
            self.mg.stop_search = True

    def wait_for_search(self):
        if self.search_thread is not None:
            self.search_thread.join()
            self.search_thread = None

    def stop_and_wait(self):
        self.stop_search()
        self.wait_for_search()

    def _start_search(self, args):
        self.stop_and_wait()

        is_white = self.board.turn == "white"
        depth, movetime = parse_go(args, is_white)
        t0 = time.perf_counter()
        callback = make_info_callback(self.mg, t0, self._emit)

        def run_search():
            best_move, score = self.mg.find_best_move(
                depth, is_white, max_time=movetime, verbose=False,
                on_depth_complete=callback,
            )
            # Opening book or sub-depth-1 timeout: emit a minimal info line
            if self.mg.last_completed_depth == 0 and best_move is not None:
                elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
                pv_str = move_to_uci(best_move)
                # score from find_best_move is white-perspective; flip to side-to-move perspective
                mover_score = score if is_white else -score
                self._emit(
                    f"info depth 1 seldepth 1 score {_format_score(mover_score)}"
                    f" nodes {self.mg.node_count} nps 0 time {elapsed_ms} pv {pv_str}"
                )
            self._emit(f"bestmove {move_to_uci(best_move)}")

        self.search_thread = threading.Thread(target=run_search, daemon=True)
        self.search_thread.start()

    def handle_line(self, line):
        line = line.strip()
        if not line:
            return True

        parts = line.split()
        command = parts[0]
        args = parts[1:]

        if command == "uci":
            self._emit("id name Suar")
            self._emit("id author Ujan Dey")
            for name, (opt_type, default, mn, mx) in _OPTIONS.items():
                self._emit(f"option name {name} type {opt_type} default {default} min {mn} max {mx}")
            self._emit("uciok")

        elif command == "setoption":
            self.stop_and_wait()
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
                        self.mg.set_hash_size(int(val_str))
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
            self._emit("readyok")

        elif command == "ucinewgame":
            self.stop_and_wait()
            self.board = Board()
            self.mg = MoveGenerator(self.board)

        elif command == "position":
            self.stop_and_wait()
            configure_position(self.board, self.mg, args)

        elif command == "go":
            self._start_search(args)

        elif command == "stop":
            self.stop_search()

        elif command == "quit":
            self.stop_and_wait()
            return False

        return True


def main():
    engine = UciEngine()

    for raw_line in sys.stdin:
        if not engine.handle_line(raw_line):
            break

        sys.stdout.flush()


if __name__ == "__main__":
    main()
