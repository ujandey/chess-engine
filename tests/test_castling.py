import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class CastlingTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.board = [
            ["r", ".", ".", ".", "k", ".", ".", "r"],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["R", ".", ".", ".", "K", ".", ".", "R"],
        ]
        self.board.turn = "white"
        self.mg = MoveGenerator(self.board)

    def test_white_queenside_castle_is_legal(self):
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertIn((7, 2), legal_moves)

    def test_white_queenside_castle_moves_rook(self):
        move_state = self.board.make_move((7, 4), (7, 2))

        self.assertEqual(self.board.get_piece(7, 2), "K")
        self.assertEqual(self.board.get_piece(7, 3), "R")
        self.assertEqual(self.board.get_piece(7, 0), ".")
        self.assertEqual(self.board.get_piece(7, 4), ".")

        self.board.undo_move((7, 4), (7, 2), move_state)

        self.assertEqual(self.board.get_piece(7, 4), "K")
        self.assertEqual(self.board.get_piece(7, 0), "R")
        self.assertEqual(self.board.get_piece(7, 3), ".")
        self.assertEqual(self.board.get_piece(7, 2), ".")


if __name__ == "__main__":
    unittest.main()
