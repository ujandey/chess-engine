import unittest

from engine.board import Board


class PawnPromotionTests(unittest.TestCase):
    def test_white_pawn_promotes_to_queen(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            ["P", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]

        move_state = board.make_move((1, 0), (0, 0))

        self.assertEqual(board.get_piece(0, 0), "Q")

        board.undo_move((1, 0), (0, 0), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")
        self.assertEqual(board.get_piece(0, 0), ".")

    def test_white_pawn_can_promote_to_knight(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            ["P", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]

        move_state = board.make_move((1, 0), (0, 0), promotion_choice="N")

        self.assertEqual(board.get_piece(0, 0), "N")

        board.undo_move((1, 0), (0, 0), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")
        self.assertEqual(board.get_piece(0, 0), ".")

    def test_black_pawn_promotes_to_queen(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["p", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]

        move_state = board.make_move((6, 0), (7, 0))

        self.assertEqual(board.get_piece(7, 0), "q")

        board.undo_move((6, 0), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 0), "p")
        self.assertEqual(board.get_piece(7, 0), ".")

    def test_black_pawn_can_promote_to_rook(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["p", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]

        move_state = board.make_move((6, 0), (7, 0), promotion_choice="R")

        self.assertEqual(board.get_piece(7, 0), "r")

        board.undo_move((6, 0), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 0), "p")
        self.assertEqual(board.get_piece(7, 0), ".")


if __name__ == "__main__":
    unittest.main()
