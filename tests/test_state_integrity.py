import random
import time
import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator
from engine.uci import UciEngine


COMPLEX_FEN = "r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def snapshot(board):
    return {
        "fen": board.to_fen(),
        "turn": board.turn,
        "hash": board.zobrist_hash,
        "piece_hash": board._piece_hash,
        "position_counts": board.position_counts.copy(),
        "piece_positions": {
            "white": set(board.piece_positions["white"]),
            "black": set(board.piece_positions["black"]),
        },
        "white_king_pos": board.white_king_pos,
        "black_king_pos": board.black_king_pos,
        "halfmove_clock": board.halfmove_clock,
        "en_passant_target": board.en_passant_target,
        "castling_rights": board.castling_rights.copy(),
    }


class SearchStateIntegrityTests(unittest.TestCase):
    def test_tiny_timeout_restores_complete_board_state(self):
        board = Board()
        board.set_fen(COMPLEX_FEN)
        mg = MoveGenerator(board)
        mg.in_opening = False
        before = snapshot(board)

        mg.find_best_move(8, board.turn == "white", max_time=0.001, verbose=False)

        self.assertEqual(snapshot(board), before)

    def test_stop_flag_restores_complete_board_state(self):
        board = Board()
        board.set_fen(COMPLEX_FEN)
        mg = MoveGenerator(board)
        mg.in_opening = False
        before = snapshot(board)

        def stop_on_first_depth(*args):
            mg.stop_search = True

        mg.find_best_move(8, board.turn == "white", verbose=False, on_depth_complete=stop_on_first_depth)

        self.assertEqual(snapshot(board), before)

    def test_generate_all_legal_moves_uses_requested_side_not_current_turn(self):
        board = Board()
        mg = MoveGenerator(board)
        board.turn = "black"

        white_moves = mg.generate_all_legal_moves(is_white=True)

        self.assertEqual(len(white_moves), 20)
        self.assertEqual(board.turn, "black")

    def test_push_pop_fuzz_restores_full_state(self):
        rng = random.Random(20260506)
        board = Board()
        mg = MoveGenerator(board)
        mg.in_opening = False
        before = snapshot(board)
        states = []

        for _ in range(32):
            moves = mg.generate_all_legal_moves(board.turn == "white")
            if not moves:
                break
            start, end, promo = rng.choice(moves)
            states.append(board.push(start, end, promo))

        for state in reversed(states):
            board.pop(state)

        self.assertEqual(snapshot(board), before)


class UciStopStateIntegrityTests(unittest.TestCase):
    def test_uci_stop_exits_and_leaves_position_unchanged(self):
        output = []
        engine = UciEngine(emit=output.append)
        engine.handle_line(f"position fen {COMPLEX_FEN}")
        before = snapshot(engine.board)

        self.assertTrue(engine.handle_line("go infinite"))
        deadline = time.perf_counter() + 1.0
        while time.perf_counter() < deadline and not engine._search_is_active():
            time.sleep(0.001)
        self.assertTrue(engine._search_is_active())

        self.assertTrue(engine.handle_line("stop"))
        engine.wait_for_search()

        self.assertFalse(engine._search_is_active())
        self.assertEqual(snapshot(engine.board), before)
        self.assertTrue(any(line.startswith("bestmove ") for line in output))


if __name__ == "__main__":
    unittest.main()
