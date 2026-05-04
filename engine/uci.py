import sys

from engine.board import Board
from engine.move_generator import MoveGenerator


STARTPOS_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


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


def apply_uci_move(board, move_text):
    start = coord_to_square(move_text[:2])
    end = coord_to_square(move_text[2:4])
    promotion = move_text[4].upper() if len(move_text) > 4 else None
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
            apply_uci_move(board, move_text)
        mg.in_opening = False


def parse_go(args):
    depth = 64
    movetime = None

    if "depth" in args:
        depth_index = args.index("depth")
        if depth_index + 1 < len(args):
            depth = int(args[depth_index + 1])

    if "movetime" in args:
        time_index = args.index("movetime")
        if time_index + 1 < len(args):
            movetime = max(0.01, int(args[time_index + 1]) / 1000.0)

    return depth, movetime


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
            print("uciok")
        elif command == "isready":
            print("readyok")
        elif command == "ucinewgame":
            board = Board()
            mg = MoveGenerator(board)
        elif command == "position":
            configure_position(board, mg, args)
        elif command == "go":
            depth, movetime = parse_go(args)
            is_white = board.turn == "white"
            best_move, score = mg.find_best_move(depth, is_white, max_time=movetime, verbose=False)
            if best_move is not None:
                print(f"info depth {mg.last_completed_depth} score cp {int(score * 100)} nodes {mg.node_count}")
            print(f"bestmove {move_to_uci(best_move)}")
        elif command == "stop":
            mg.stop_search = True
        elif command == "quit":
            break

        sys.stdout.flush()


if __name__ == "__main__":
    main()
