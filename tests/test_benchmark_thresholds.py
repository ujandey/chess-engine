import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class BenchmarkThresholdTests(unittest.TestCase):
    def test_depth_two_search_has_minimum_throughput(self):
        board = Board()
        board.set_fen("r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        mg = MoveGenerator(board)
        mg.in_opening = False

        move, _ = mg.find_best_move(2, board.turn == "white", verbose=False)

        self.assertIsNotNone(move)
        self.assertGreater(mg.node_count, 0)
        self.assertGreater(mg.last_completed_depth, 0)
        self.assertGreaterEqual(mg.node_count / max(mg.last_search_time, 0.001), 500)

    def test_endgame_depth_three_stays_fast(self):
        board = Board()
        board.set_fen("8/2p5/3p4/3Pp3/2P1P3/6k1/8/6K1 w - - 0 1")
        mg = MoveGenerator(board)
        mg.in_opening = False

        move, _ = mg.find_best_move(3, board.turn == "white", verbose=False)

        self.assertIsNotNone(move)
        self.assertLess(mg.last_search_time, 1.0)


if __name__ == "__main__":
    unittest.main()
