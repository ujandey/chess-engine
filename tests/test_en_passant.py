import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class EnPassantTests(unittest.TestCase):
    # ------------------------------------------------------------------
    # En passant target is set correctly
    # ------------------------------------------------------------------

    def test_en_passant_target_set_after_white_two_square_push(self):
        board = Board()
        board.make_move((6, 4), (4, 4))
        self.assertEqual(board.en_passant_target, (5, 4))

    def test_en_passant_target_set_after_black_two_square_push(self):
        board = Board()
        board.make_move((1, 3), (3, 3))
        self.assertEqual(board.en_passant_target, (2, 3))

    def test_en_passant_target_cleared_after_any_other_move(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "p", "P", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.en_passant_target = (2, 3)
        board.make_move((7, 4), (7, 3))  # king moves instead
        self.assertIsNone(board.en_passant_target)

    # ------------------------------------------------------------------
    # White captures en passant
    # ------------------------------------------------------------------

    def test_white_en_passant_capture_left(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "p", "P", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.en_passant_target = (2, 3)
        board.turn = "white"
        mg = MoveGenerator(board)

        self.assertIn((2, 3), mg.get_legal_moves(3, 4))

        move_state = board.make_move((3, 4), (2, 3))
        self.assertEqual(board.get_piece(2, 3), "P")  # white pawn arrived
        self.assertEqual(board.get_piece(3, 3), ".")  # captured pawn removed
        self.assertEqual(board.get_piece(3, 4), ".")  # original square empty

        board.undo_move((3, 4), (2, 3), move_state)
        self.assertEqual(board.get_piece(3, 4), "P")
        self.assertEqual(board.get_piece(3, 3), "p")  # captured pawn restored
        self.assertEqual(board.get_piece(2, 3), ".")

    def test_white_en_passant_capture_right(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "P", "p", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.en_passant_target = (2, 4)
        board.turn = "white"
        mg = MoveGenerator(board)

        self.assertIn((2, 4), mg.get_legal_moves(3, 3))

        move_state = board.make_move((3, 3), (2, 4))
        self.assertEqual(board.get_piece(2, 4), "P")
        self.assertEqual(board.get_piece(3, 4), ".")  # captured pawn removed
        self.assertEqual(board.get_piece(3, 3), ".")

        board.undo_move((3, 3), (2, 4), move_state)
        self.assertEqual(board.get_piece(3, 3), "P")
        self.assertEqual(board.get_piece(3, 4), "p")

    # ------------------------------------------------------------------
    # Black captures en passant
    # ------------------------------------------------------------------

    def test_black_en_passant_capture_right(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "p", "P", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.en_passant_target = (5, 4)
        board.turn = "black"
        mg = MoveGenerator(board)

        self.assertIn((5, 4), mg.get_legal_moves(4, 3))

        move_state = board.make_move((4, 3), (5, 4))
        self.assertEqual(board.get_piece(5, 4), "p")
        self.assertEqual(board.get_piece(4, 4), ".")  # white pawn removed
        self.assertEqual(board.get_piece(4, 3), ".")

        board.undo_move((4, 3), (5, 4), move_state)
        self.assertEqual(board.get_piece(4, 3), "p")
        self.assertEqual(board.get_piece(4, 4), "P")

    def test_black_en_passant_capture_left(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "P", "p", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.en_passant_target = (5, 3)
        board.turn = "black"
        mg = MoveGenerator(board)

        self.assertIn((5, 3), mg.get_legal_moves(4, 4))

        move_state = board.make_move((4, 4), (5, 3))
        self.assertEqual(board.get_piece(5, 3), "p")
        self.assertEqual(board.get_piece(4, 3), ".")  # white pawn removed

        board.undo_move((4, 4), (5, 3), move_state)
        self.assertEqual(board.get_piece(4, 4), "p")
        self.assertEqual(board.get_piece(4, 3), "P")

    # ------------------------------------------------------------------
    # En passant is not available without the target set
    # ------------------------------------------------------------------

    def test_en_passant_not_available_without_target(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "p", "P", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.en_passant_target = None
        board.turn = "white"
        mg = MoveGenerator(board)
        self.assertNotIn((2, 3), mg.get_legal_moves(3, 4))

    # ------------------------------------------------------------------
    # En passant is not available if it would leave the king in check
    # ------------------------------------------------------------------

    def test_en_passant_filtered_when_leaves_king_in_check(self):
        # Classic en passant absolute pin on a rank.
        # White king at h4 (4,7), black rook at a4 (4,0).
        # White pawn at e4 (4,4), black pawn at d4 (4,3).
        # Capturing en passant moves the white pawn off rank 4 and removes the
        # black pawn from rank 4, leaving the rook a clear line to the king.
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["r", ".", ".", "p", "P", ".", ".", "K"],  # all on rank 4
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
        ]
        # en_passant_target is the square the capturing pawn lands on.
        # White pawn at (4,4) captures left to (3,3); black pawn at (4,3) is removed.
        board.en_passant_target = (3, 3)
        board.turn = "white"
        mg = MoveGenerator(board)

        legal = mg.get_legal_moves(4, 4)
        self.assertNotIn((3, 3), legal)


if __name__ == "__main__":
    unittest.main()
