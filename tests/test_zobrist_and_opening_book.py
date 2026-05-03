import unittest
from unittest import mock

from engine.board import Board
import engine.opening_book as opening_book


def make_board(rows, turn="white", castling_rights=None, en_passant_target=None, halfmove_clock=0):
    board = Board()
    board.board = rows
    board.turn = turn
    board.castling_rights = castling_rights or {
        "white_kingside": False,
        "white_queenside": False,
        "black_kingside": False,
        "black_queenside": False,
    }
    board.en_passant_target = en_passant_target
    board.halfmove_clock = halfmove_clock
    board.refresh_zobrist_hash()
    board.position_counts = {board.get_position_key(): 1}
    return board


def snapshot(board):
    return {
        "board": [row[:] for row in board.board],
        "turn": board.turn,
        "castling_rights": board.castling_rights.copy(),
        "en_passant_target": board.en_passant_target,
        "halfmove_clock": board.halfmove_clock,
        "white_king_pos": board.white_king_pos,
        "black_king_pos": board.black_king_pos,
        "piece_positions": {
            "white": set(board.piece_positions["white"]),
            "black": set(board.piece_positions["black"]),
        },
        "piece_hash": board._piece_hash,
        "zobrist_hash": board.zobrist_hash,
    }


class ZobristReversibilityTests(unittest.TestCase):
    def assert_move_restores_snapshot(self, board, start, end, promotion_choice=None):
        before = snapshot(board)
        move_state = board.make_move(start, end, promotion_choice)
        board.undo_move(start, end, move_state)

        self.assertEqual(snapshot(board), before)

    def test_quiet_move_capture_castling_promotion_and_en_passant_restore_hash(self):
        self.assert_move_restores_snapshot(Board(), (7, 6), (5, 5))

        capture_board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", "p", ".", ".", ".", "."],
                [".", ".", ".", ".", "P", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ]
        )
        self.assert_move_restores_snapshot(capture_board, (4, 4), (3, 3))

        castling_board = make_board(
            [
                ["r", ".", ".", ".", "k", ".", ".", "r"],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                ["R", ".", ".", ".", "K", ".", ".", "R"],
            ],
            castling_rights={
                "white_kingside": True,
                "white_queenside": True,
                "black_kingside": True,
                "black_queenside": True,
            },
        )
        self.assert_move_restores_snapshot(castling_board, (7, 4), (7, 6))
        self.assert_move_restores_snapshot(castling_board, (7, 4), (7, 2))

        promotion_board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                ["P", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ],
            halfmove_clock=12,
        )
        self.assert_move_restores_snapshot(promotion_board, (1, 0), (0, 0), "N")

        en_passant_board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", "p", "P", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ],
            en_passant_target=(2, 3),
        )
        self.assert_move_restores_snapshot(en_passant_board, (3, 4), (2, 3))


class OpeningBookFallbackTests(unittest.TestCase):
    def setUp(self):
        self.previous_reader = opening_book._book_reader
        self.previous_attempted = opening_book._book_load_attempted

    def tearDown(self):
        opening_book._book_reader = self.previous_reader
        opening_book._book_load_attempted = self.previous_attempted

    def test_get_book_move_returns_none_without_python_chess(self):
        with mock.patch.object(opening_book, "chess", None):
            self.assertIsNone(opening_book.get_book_move(Board()))

    def test_get_book_move_returns_none_when_reader_cannot_load(self):
        opening_book._book_reader = None
        opening_book._book_load_attempted = False

        with mock.patch.object(opening_book.chess.polyglot, "open_reader", side_effect=OSError):
            self.assertIsNone(opening_book.get_book_move(Board()))

        self.assertTrue(opening_book._book_load_attempted)
        self.assertIsNone(opening_book._book_reader)

    def test_get_book_move_returns_none_after_book_move_limit(self):
        board = Board()
        board.position_counts = {board.get_position_key(): opening_book.MAX_BOOK_MOVES * 2 + 1}

        with mock.patch.object(opening_book, "_get_book_reader") as get_reader:
            self.assertIsNone(opening_book.get_book_move(board))

        get_reader.assert_not_called()

    def test_get_book_move_returns_none_when_lookup_raises(self):
        reader = mock.Mock()
        reader.find_all.side_effect = ValueError

        with mock.patch.object(opening_book, "_get_book_reader", return_value=reader):
            self.assertIsNone(opening_book.get_book_move(Board()))


if __name__ == "__main__":
    unittest.main()
