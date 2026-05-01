import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator


class PerftTests(unittest.TestCase):
    def test_start_position_perft(self):
        board = Board()
        mg = MoveGenerator(board)

        self.assertEqual(mg.perft(1), 20)
        self.assertEqual(mg.perft(2), 400)
        self.assertEqual(mg.perft(3), 8902)

    def test_kiwipete_perft(self):
        board = Board()
        board.set_fen("r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        mg = MoveGenerator(board)

        self.assertEqual(mg.perft(1), 48)
        self.assertEqual(mg.perft(2), 1991)


if __name__ == "__main__":
    unittest.main()
