import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator
from ui.gui import _board_from_snapshot, _score_to_ratio


class GuiEvalTests(unittest.TestCase):
    def test_score_to_ratio_shows_terminal_results_at_extremes(self):
        self.assertEqual(_score_to_ratio(1000), 1.0)
        self.assertEqual(_score_to_ratio(-1000), 0.0)
        self.assertEqual(_score_to_ratio(0), 0.5)

    def test_board_from_snapshot_refreshes_search_caches(self):
        source = Board()
        source.set_fen("4k3/8/8/8/8/8/8/R3K2R w KQ - 17 42")
        snapshot = {
            "board": [row[:] for row in source.board],
            "turn": source.turn,
            "en_passant_target": source.en_passant_target,
            "halfmove_clock": source.halfmove_clock,
            "castling_rights": source.castling_rights.copy(),
            "position_counts": source.position_counts.copy(),
        }

        restored = _board_from_snapshot(snapshot)

        self.assertEqual(restored.white_king_pos, (7, 4))
        self.assertEqual(restored.black_king_pos, (0, 4))
        self.assertIn((7, 0), restored.piece_positions["white"])
        self.assertIn((7, 7), restored.piece_positions["white"])
        self.assertEqual(restored.zobrist_hash, source.zobrist_hash)
        self.assertEqual(
            MoveGenerator(restored).evaluate_position(),
            MoveGenerator(source).evaluate_position(),
        )


if __name__ == "__main__":
    unittest.main()
