import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


def make_castling_board():
    board = Board()
    board.board = [
        ["r", ".", ".", ".", "k", ".", ".", "r"],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        ["R", ".", ".", ".", "K", ".", ".", "R"],
    ]
    board.castling_rights = {
        "white_kingside": True,
        "white_queenside": True,
        "black_kingside": True,
        "black_queenside": True,
    }
    return board


class CastlingTests(unittest.TestCase):
    def setUp(self):
        self.board = make_castling_board()
        self.board.turn = "white"
        self.mg = MoveGenerator(self.board)

    # ------------------------------------------------------------------
    # White queenside
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # White kingside
    # ------------------------------------------------------------------

    def test_white_kingside_castle_is_legal(self):
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertIn((7, 6), legal_moves)

    def test_white_kingside_castle_moves_rook(self):
        move_state = self.board.make_move((7, 4), (7, 6))

        self.assertEqual(self.board.get_piece(7, 6), "K")
        self.assertEqual(self.board.get_piece(7, 5), "R")
        self.assertEqual(self.board.get_piece(7, 7), ".")
        self.assertEqual(self.board.get_piece(7, 4), ".")

        self.board.undo_move((7, 4), (7, 6), move_state)

        self.assertEqual(self.board.get_piece(7, 4), "K")
        self.assertEqual(self.board.get_piece(7, 7), "R")
        self.assertEqual(self.board.get_piece(7, 5), ".")
        self.assertEqual(self.board.get_piece(7, 6), ".")

    # ------------------------------------------------------------------
    # Black queenside
    # ------------------------------------------------------------------

    def test_black_queenside_castle_is_legal(self):
        self.board.turn = "black"
        legal_moves = self.mg.get_legal_moves(0, 4)
        self.assertIn((0, 2), legal_moves)

    def test_black_queenside_castle_moves_rook(self):
        self.board.turn = "black"
        move_state = self.board.make_move((0, 4), (0, 2))

        self.assertEqual(self.board.get_piece(0, 2), "k")
        self.assertEqual(self.board.get_piece(0, 3), "r")
        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(self.board.get_piece(0, 4), ".")

        self.board.undo_move((0, 4), (0, 2), move_state)

        self.assertEqual(self.board.get_piece(0, 4), "k")
        self.assertEqual(self.board.get_piece(0, 0), "r")
        self.assertEqual(self.board.get_piece(0, 3), ".")
        self.assertEqual(self.board.get_piece(0, 2), ".")

    # ------------------------------------------------------------------
    # Black kingside
    # ------------------------------------------------------------------

    def test_black_kingside_castle_is_legal(self):
        self.board.turn = "black"
        legal_moves = self.mg.get_legal_moves(0, 4)
        self.assertIn((0, 6), legal_moves)

    def test_black_kingside_castle_moves_rook(self):
        self.board.turn = "black"
        move_state = self.board.make_move((0, 4), (0, 6))

        self.assertEqual(self.board.get_piece(0, 6), "k")
        self.assertEqual(self.board.get_piece(0, 5), "r")
        self.assertEqual(self.board.get_piece(0, 7), ".")

        self.board.undo_move((0, 4), (0, 6), move_state)

        self.assertEqual(self.board.get_piece(0, 4), "k")
        self.assertEqual(self.board.get_piece(0, 7), "r")
        self.assertEqual(self.board.get_piece(0, 5), ".")

    # ------------------------------------------------------------------
    # Cannot castle when in check
    # ------------------------------------------------------------------

    def test_cannot_castle_when_in_check(self):
        self.board.board[3][4] = "r"  # black rook on e-file attacks white king
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertNotIn((7, 6), legal_moves)
        self.assertNotIn((7, 2), legal_moves)

    # ------------------------------------------------------------------
    # Cannot castle through an attacked square
    # ------------------------------------------------------------------

    def test_cannot_castle_kingside_through_attacked_square(self):
        self.board.board[3][5] = "r"  # black rook attacks f1 (7,5)
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertNotIn((7, 6), legal_moves)
        self.assertIn((7, 2), legal_moves)

    def test_cannot_castle_queenside_through_attacked_square(self):
        self.board.board[3][3] = "r"  # black rook attacks d1 (7,3)
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertNotIn((7, 2), legal_moves)
        self.assertIn((7, 6), legal_moves)

    # ------------------------------------------------------------------
    # Cannot castle when path is occupied
    # ------------------------------------------------------------------

    def test_cannot_castle_kingside_when_path_occupied(self):
        self.board.board[7][5] = "B"  # own piece on f1
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertNotIn((7, 6), legal_moves)
        self.assertIn((7, 2), legal_moves)

    def test_cannot_castle_queenside_when_path_occupied(self):
        self.board.board[7][1] = "N"  # own piece on b1
        legal_moves = self.mg.get_legal_moves(7, 4)
        self.assertNotIn((7, 2), legal_moves)
        self.assertIn((7, 6), legal_moves)

    # ------------------------------------------------------------------
    # Castling rights removed after king or rook moves
    # ------------------------------------------------------------------

    def test_castling_rights_lost_after_white_king_moves(self):
        move_state = self.board.make_move((7, 4), (7, 3))
        self.assertFalse(self.board.castling_rights["white_kingside"])
        self.assertFalse(self.board.castling_rights["white_queenside"])

        self.board.undo_move((7, 4), (7, 3), move_state)
        self.assertTrue(self.board.castling_rights["white_kingside"])
        self.assertTrue(self.board.castling_rights["white_queenside"])

    def test_castling_rights_lost_after_kingside_rook_moves(self):
        move_state = self.board.make_move((7, 7), (7, 6))
        self.assertFalse(self.board.castling_rights["white_kingside"])
        self.assertTrue(self.board.castling_rights["white_queenside"])

        self.board.undo_move((7, 7), (7, 6), move_state)
        self.assertTrue(self.board.castling_rights["white_kingside"])

    def test_castling_rights_lost_after_queenside_rook_moves(self):
        move_state = self.board.make_move((7, 0), (7, 1))
        self.assertFalse(self.board.castling_rights["white_queenside"])
        self.assertTrue(self.board.castling_rights["white_kingside"])

        self.board.undo_move((7, 0), (7, 1), move_state)
        self.assertTrue(self.board.castling_rights["white_queenside"])


if __name__ == "__main__":
    unittest.main()
