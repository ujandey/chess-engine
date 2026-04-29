import unittest

from engine.board import Board


def make_promotion_board(pawn, pawn_row, pawn_col):
    board = Board()
    board.board = [
        [".", ".", ".", ".", "k", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", "K", ".", ".", "."],
    ]
    board.board[pawn_row][pawn_col] = pawn
    return board


class PawnPromotionTests(unittest.TestCase):
    def test_white_pawn_promotes_to_queen(self):
        board = make_promotion_board("P", 1, 0)
        move_state = board.make_move((1, 0), (0, 0))
        self.assertEqual(board.get_piece(0, 0), "Q")
        board.undo_move((1, 0), (0, 0), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")
        self.assertEqual(board.get_piece(0, 0), ".")

    def test_white_pawn_can_promote_to_knight(self):
        board = make_promotion_board("P", 1, 0)
        move_state = board.make_move((1, 0), (0, 0), promotion_choice="N")
        self.assertEqual(board.get_piece(0, 0), "N")
        board.undo_move((1, 0), (0, 0), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")
        self.assertEqual(board.get_piece(0, 0), ".")

    def test_white_pawn_can_promote_to_bishop(self):
        board = make_promotion_board("P", 1, 0)
        move_state = board.make_move((1, 0), (0, 0), promotion_choice="B")
        self.assertEqual(board.get_piece(0, 0), "B")
        board.undo_move((1, 0), (0, 0), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")

    def test_white_pawn_can_promote_to_rook(self):
        board = make_promotion_board("P", 1, 0)
        move_state = board.make_move((1, 0), (0, 0), promotion_choice="R")
        self.assertEqual(board.get_piece(0, 0), "R")
        board.undo_move((1, 0), (0, 0), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")

    def test_black_pawn_promotes_to_queen(self):
        board = make_promotion_board("p", 6, 0)
        move_state = board.make_move((6, 0), (7, 0))
        self.assertEqual(board.get_piece(7, 0), "q")
        board.undo_move((6, 0), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 0), "p")
        self.assertEqual(board.get_piece(7, 0), ".")

    def test_black_pawn_can_promote_to_rook(self):
        board = make_promotion_board("p", 6, 0)
        move_state = board.make_move((6, 0), (7, 0), promotion_choice="R")
        self.assertEqual(board.get_piece(7, 0), "r")
        board.undo_move((6, 0), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 0), "p")
        self.assertEqual(board.get_piece(7, 0), ".")

    def test_black_pawn_can_promote_to_bishop(self):
        board = make_promotion_board("p", 6, 0)
        move_state = board.make_move((6, 0), (7, 0), promotion_choice="B")
        self.assertEqual(board.get_piece(7, 0), "b")
        board.undo_move((6, 0), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 0), "p")

    def test_black_pawn_can_promote_to_knight(self):
        board = make_promotion_board("p", 6, 0)
        move_state = board.make_move((6, 0), (7, 0), promotion_choice="N")
        self.assertEqual(board.get_piece(7, 0), "n")
        board.undo_move((6, 0), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 0), "p")

    def test_white_pawn_promotes_via_diagonal_capture(self):
        board = make_promotion_board("P", 1, 0)
        board.board[0][1] = "r"  # black rook on b8 to capture
        move_state = board.make_move((1, 0), (0, 1))
        self.assertEqual(board.get_piece(0, 1), "Q")
        board.undo_move((1, 0), (0, 1), move_state)
        self.assertEqual(board.get_piece(1, 0), "P")
        self.assertEqual(board.get_piece(0, 1), "r")

    def test_black_pawn_promotes_via_diagonal_capture(self):
        board = make_promotion_board("p", 6, 1)
        board.board[7][0] = "R"  # white rook on a1 to capture
        move_state = board.make_move((6, 1), (7, 0))
        self.assertEqual(board.get_piece(7, 0), "q")
        board.undo_move((6, 1), (7, 0), move_state)
        self.assertEqual(board.get_piece(6, 1), "p")
        self.assertEqual(board.get_piece(7, 0), "R")

    def test_invalid_promotion_choice_defaults_to_queen(self):
        board = make_promotion_board("P", 1, 0)
        board.make_move((1, 0), (0, 0), promotion_choice="X")
        self.assertEqual(board.get_piece(0, 0), "Q")


if __name__ == "__main__":
    unittest.main()
