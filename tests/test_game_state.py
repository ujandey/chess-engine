import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class GameStateTests(unittest.TestCase):
    def test_checkmate_detection(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", ".", ".", ".", "k"],
            [".", ".", ".", ".", ".", ".", "Q", "."],
            [".", ".", ".", ".", ".", "K", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
        ]
        board.turn = "black"
        mg = MoveGenerator(board)

        status = mg.get_game_status()

        self.assertTrue(mg.is_checkmate(False))
        self.assertEqual(status["result"], "checkmate")

    def test_stalemate_detection(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", ".", ".", ".", "k"],
            [".", ".", ".", ".", ".", "K", ".", "."],
            [".", ".", ".", ".", ".", ".", "Q", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
        ]
        board.turn = "black"
        mg = MoveGenerator(board)

        status = mg.get_game_status()

        self.assertTrue(mg.is_stalemate(False))
        self.assertEqual(status["result"], "stalemate")

    def test_insufficient_material_detection(self):
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
        mg = MoveGenerator(board)

        status = mg.get_game_status()

        self.assertTrue(mg.is_insufficient_material())
        self.assertEqual(status["result"], "insufficient_material")

    def test_insufficient_material_knight_vs_knight(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", "n", "."],
            [".", ".", ".", ".", "K", ".", "N", "."],
        ]
        mg = MoveGenerator(board)

        status = mg.get_game_status()

        self.assertTrue(mg.is_insufficient_material())
        self.assertEqual(status["result"], "insufficient_material")

    def test_insufficient_material_same_color_bishops(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "b"],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["B", ".", ".", ".", "K", ".", ".", "."],
        ]
        mg = MoveGenerator(board)

        status = mg.get_game_status()

        self.assertTrue(mg.is_insufficient_material())
        self.assertEqual(status["result"], "insufficient_material")

    def test_fifty_move_rule_detection(self):
        board = Board()
        board.halfmove_clock = 100
        mg = MoveGenerator(board)

        status = mg.get_game_status()

        self.assertTrue(mg.is_fifty_move_draw())
        self.assertEqual(status["result"], "fifty_move_rule")

    def test_halfmove_clock_resets_on_pawn_move(self):
        board = Board()
        board.halfmove_clock = 80

        move_state = board.make_move((6, 4), (4, 4))

        self.assertEqual(board.halfmove_clock, 0)

        board.undo_move((6, 4), (4, 4), move_state)
        self.assertEqual(board.halfmove_clock, 80)

    def test_halfmove_clock_increments_on_quiet_move(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "R"],
        ]
        board.halfmove_clock = 12

        move_state = board.make_move((7, 7), (7, 6))

        self.assertEqual(board.halfmove_clock, 13)

        board.undo_move((7, 7), (7, 6), move_state)
        self.assertEqual(board.halfmove_clock, 12)


if __name__ == "__main__":
    unittest.main()
