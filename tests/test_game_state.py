import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class GameStateTests(unittest.TestCase):
    def test_evaluation_equal_material_is_zero(self):
        board = Board()
        mg = MoveGenerator(board)

        self.assertEqual(mg.evaluate_position(), 0)

    def test_evaluation_extra_white_queen_is_positive(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", "Q", "K", ".", ".", "."],
        ]
        mg = MoveGenerator(board)

        self.assertGreater(mg.evaluate_position(), 0)

    def test_evaluation_checkmate_is_decisive(self):
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

        self.assertEqual(mg.evaluate_position(), 1000)

    def test_evaluation_checkmate_is_depth_aware(self):
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

        self.assertEqual(mg.evaluate_position(depth=0), 1000)
        self.assertEqual(mg.evaluate_position(depth=3), 997)

    def test_evaluation_checkmated_side_is_negative(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", "k", ".", "."],
            [".", ".", ".", ".", ".", ".", "q", "."],
            [".", ".", ".", ".", ".", ".", ".", "K"],
        ]
        board.turn = "white"
        mg = MoveGenerator(board)

        self.assertEqual(mg.evaluate_position(depth=2), -998)

    def test_search_mate_score_uses_ply_distance(self):
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
        board.refresh_zobrist_hash()
        mg = MoveGenerator(board)

        self.assertEqual(mg.negamax(depth=5, is_white_turn=False, ply=2), -998)

    def test_search_uses_board_repetition_counts_for_current_line(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", "N", ".", "."],
            [".", ".", ".", ".", "P", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "."],
        ]
        board.turn = "black"
        board.refresh_zobrist_hash()
        key = board.zobrist_hash
        board.position_counts = {key: 3}
        mg = MoveGenerator(board)

        self.assertEqual(mg.negamax(depth=1, is_white_turn=False), 0)
        self.assertEqual(board.position_counts, {key: 3})

    def test_evaluation_is_white_perspective_for_material(self):
        board = Board()
        board.board = [
            [".", ".", ".", ".", "k", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", "K", ".", ".", "r"],
        ]
        board.turn = "black"
        mg = MoveGenerator(board)

        self.assertLess(mg.evaluate_position(), 0)

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

    def test_threefold_repetition_detection(self):
        board = Board()
        mg = MoveGenerator(board)

        moves = [
            ((7, 6), (5, 5)),  # white knight g1 -> f3
            ((0, 6), (2, 5)),  # black knight g8 -> f6
            ((5, 5), (7, 6)),  # white knight f3 -> g1
            ((2, 5), (0, 6)),  # black knight f6 -> g8
            ((7, 6), (5, 5)),
            ((0, 6), (2, 5)),
            ((5, 5), (7, 6)),
            ((2, 5), (0, 6)),
        ]

        for start, end in moves:
            board.move_piece(start, end)

        status = mg.get_game_status()

        self.assertTrue(mg.is_threefold_repetition())
        self.assertEqual(status["result"], "threefold_repetition")
        self.assertGreaterEqual(board.position_counts[board.get_position_key()], 3)

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

    def test_push_and_pop_own_turn_repetition_halfmove_and_hash(self):
        board = Board()
        start_hash = board.zobrist_hash
        start_counts = board.position_counts.copy()

        move_state = board.push((6, 4), (4, 4))

        self.assertEqual(board.turn, "black")
        self.assertEqual(board.halfmove_clock, 0)
        self.assertEqual(board.get_piece(4, 4), "P")
        self.assertEqual(board.position_counts[board.zobrist_hash], 1)
        self.assertNotEqual(board.zobrist_hash, start_hash)

        board.pop(move_state)

        self.assertEqual(board.turn, "white")
        self.assertEqual(board.halfmove_clock, 0)
        self.assertEqual(board.get_piece(6, 4), "P")
        self.assertEqual(board.get_piece(4, 4), ".")
        self.assertEqual(board.zobrist_hash, start_hash)
        self.assertEqual(board.position_counts, start_counts)


if __name__ == "__main__":
    unittest.main()
