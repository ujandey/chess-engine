import random
from pathlib import Path

try:
    import chess
    import chess.polyglot
except ImportError:
    chess = None


BOOK_PATH = Path(__file__).resolve().parent.parent / "Titans" / "Titans.bin"
MAX_BOOK_MOVES = 15
MAX_WEIGHTED_CANDIDATES = 3

_book_reader = None
_book_load_attempted = False


def convert_to_chess_board(custom_board):
    if chess is None:
        raise RuntimeError("python-chess is required for Polyglot opening books")

    return chess.Board(custom_board.to_fen(halfmove_clock=0, fullmove_number=1))


def _played_plies(board):
    return max(0, sum(board.position_counts.values()) - 1)


def _get_book_reader():
    global _book_reader, _book_load_attempted

    if chess is None:
        return None

    if _book_load_attempted:
        return _book_reader

    _book_load_attempted = True
    try:
        _book_reader = chess.polyglot.open_reader(str(BOOK_PATH))
    except (OSError, ValueError):
        _book_reader = None

    return _book_reader


def _polyglot_move_to_engine_move(move):
    start = (7 - chess.square_rank(move.from_square), chess.square_file(move.from_square))
    end = (7 - chess.square_rank(move.to_square), chess.square_file(move.to_square))
    return start, end


def get_book_move(board):
    if _played_plies(board) >= MAX_BOOK_MOVES * 2:
        return None

    reader = _get_book_reader()
    if reader is None:
        return None

    try:
        chess_board = convert_to_chess_board(board)
        entries = list(reader.find_all(chess_board))
    except (ValueError, IndexError, KeyError, OSError):
        return None

    if not entries:
        return None

    entries = sorted(entries, key=lambda entry: entry.weight, reverse=True)
    entries = entries[:MAX_WEIGHTED_CANDIDATES]

    weights = [entry.weight for entry in entries]
    if sum(weights) > 0:
        selected = random.choices(entries, weights=weights, k=1)[0]
    else:
        selected = random.choice(entries)

    return _polyglot_move_to_engine_move(selected.move)
