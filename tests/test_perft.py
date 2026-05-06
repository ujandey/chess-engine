import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class PerftTests(unittest.TestCase):
    CASES = [
        (
            "startpos",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            {1: 20, 2: 400, 3: 8902, 4: 197281},
        ),
        (
            "kiwipete",
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            {1: 48, 2: 2039, 3: 97862},
        ),
        (
            "endgame_ep",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            {1: 14, 2: 191, 3: 2812, 4: 43238},
        ),
        (
            # CPW Position 5: exercises all promotion types
            "promotions",
            "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
            {1: 24, 2: 496, 3: 9483},
        ),
    ]

    def test_perft_regression_positions(self):
        for name, fen, expected_by_depth in self.CASES:
            with self.subTest(position=name):
                board = Board()
                board.set_fen(fen)
                mg = MoveGenerator(board)

                for depth, expected in expected_by_depth.items():
                    with self.subTest(position=name, depth=depth):
                        self.assertEqual(mg.perft(depth), expected)

    def test_perft_divide_sums_to_perft(self):
        board = Board()
        board.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        mg = MoveGenerator(board)

        self.assertEqual(sum(nodes for _, nodes in mg.perft_divide(2)), mg.perft(2))


if __name__ == "__main__":
    unittest.main()
