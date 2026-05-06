import threading
import time
import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator
from engine.notation import move_to_san
from engine.uci import (
    UciEngine,
    apply_uci_move,
    configure_position,
    coord_to_square,
    move_to_uci,
    parse_go,
    square_to_coord,
)
from ui.gui import ChessGUI, GameNode


def make_board(rows, turn="white", castling_rights=None, en_passant_target=None):
    board = Board()
    board.board = rows
    board.turn = turn
    board.castling_rights = castling_rights or {
        "white_kingside": False,
        "white_queenside": False,
        "black_kingside": False,
        "black_queenside": False,
    }
    board.en_passant_target = en_passant_target
    board.refresh_zobrist_hash()
    board.position_counts = {board.get_position_key(): 1}
    return board


class SanTests(unittest.TestCase):
    def test_pawn_push_san(self):
        board = Board()
        mg = MoveGenerator(board)

        self.assertEqual(move_to_san(board, mg, (6, 4), (4, 4)), "e4")

    def test_castling_san(self):
        board = make_board(
            [
                ["r", ".", ".", ".", "k", ".", ".", "r"],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                ["R", ".", ".", ".", "K", ".", ".", "R"],
            ],
            castling_rights={
                "white_kingside": True,
                "white_queenside": True,
                "black_kingside": True,
                "black_queenside": True,
            },
        )
        mg = MoveGenerator(board)

        self.assertEqual(move_to_san(board, mg, (7, 4), (7, 6)), "O-O")
        self.assertEqual(move_to_san(board, mg, (7, 4), (7, 2)), "O-O-O")

    def test_castling_san_includes_check_suffix(self):
        board = make_board(
            [
                [".", ".", ".", ".", ".", "k", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "R"],
            ],
            castling_rights={
                "white_kingside": True,
                "white_queenside": False,
                "black_kingside": False,
                "black_queenside": False,
            },
        )
        mg = MoveGenerator(board)

        self.assertEqual(move_to_san(board, mg, (7, 4), (7, 6)), "O-O+")

    def test_capture_promotion_and_checkmate_san(self):
        board = make_board(
            [
                [".", "r", ".", ".", "k", ".", ".", "."],
                ["P", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ]
        )
        mg = MoveGenerator(board)
        self.assertEqual(move_to_san(board, mg, (1, 0), (0, 1), "N"), "axb8=N")

        mate_board = make_board(
            [
                [".", ".", ".", ".", ".", ".", ".", "k"],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", "K", "Q", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
            ]
        )
        mate_mg = MoveGenerator(mate_board)

        self.assertEqual(move_to_san(mate_board, mate_mg, (2, 6), (1, 6)), "Qg7#")

    def test_piece_disambiguation_san(self):
        board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", "N", ".", ".", ".", "N", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ]
        )
        mg = MoveGenerator(board)

        self.assertEqual(move_to_san(board, mg, (5, 5), (6, 3)), "Nfd2")


class PgnVariationTests(unittest.TestCase):
    def test_pgn_tokens_include_inline_variations(self):
        root = GameNode({}, move_san="")
        e4 = GameNode({}, move=((6, 4), (4, 4), None), move_san="e4", parent=root)
        d4 = GameNode({}, move=((6, 3), (4, 3), None), move_san="d4", parent=root)
        e5 = GameNode({}, move=((1, 4), (3, 4), None), move_san="e5", parent=e4)
        root.children = [e4, d4]
        e4.children = [e5]

        gui = object.__new__(ChessGUI)

        self.assertEqual(
            gui._pgn_tokens(root, 1, True, after_var=False),
            ["1.", "e4", "(", "1.", "d4", ")", "1...", "e5"],
        )


class UciParsingTests(unittest.TestCase):
    def test_square_and_move_conversion(self):
        self.assertEqual(square_to_coord((7, 4)), "e1")
        self.assertEqual(coord_to_square("e4"), (4, 4))
        self.assertEqual(move_to_uci(((6, 4), (4, 4))), "e2e4")
        self.assertEqual(move_to_uci(None), "0000")

    def test_parse_go_depth_and_movetime(self):
        self.assertEqual(parse_go(["depth", "5"], True), (5, None))
        self.assertEqual(parse_go(["movetime", "250"], True), (64, 0.25))
        self.assertEqual(parse_go(["depth", "3", "movetime", "1"], True), (3, 0.01))

    def test_parse_go_infinite(self):
        self.assertEqual(parse_go(["infinite"], True), (64, None))
        self.assertEqual(parse_go(["infinite"], False), (64, None))

    def test_parse_go_wtime_btime(self):
        _, wt = parse_go(["wtime", "60000", "btime", "60000"], True)
        self.assertIsNotNone(wt)
        self.assertGreater(wt, 0.0)
        self.assertLessEqual(wt, 30.0)

        _, bt = parse_go(["wtime", "60000", "btime", "60000"], False)
        self.assertIsNotNone(bt)
        self.assertGreater(bt, 0.0)

    def test_configure_position_startpos_with_moves(self):
        board = Board()
        mg = MoveGenerator(board)

        configure_position(board, mg, ["startpos", "moves", "e2e4", "e7e5", "g1f3"])

        self.assertEqual(board.get_piece(4, 4), "P")
        self.assertEqual(board.get_piece(3, 4), "p")
        self.assertEqual(board.get_piece(5, 5), "N")
        self.assertEqual(board.turn, "black")
        self.assertFalse(mg.in_opening)

    def test_apply_uci_move_handles_promotion(self):
        board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                ["P", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ]
        )

        apply_uci_move(board, None, "a7a8n")

        self.assertEqual(board.get_piece(0, 0), "N")
        self.assertEqual(board.turn, "black")

    def test_apply_uci_move_rejects_invalid_promotion(self):
        board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                ["P", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ]
        )
        apply_uci_move(board, None, "a7a8x")
        # pawn must still be on a7; move was rejected
        self.assertEqual(board.get_piece(1, 0), "P")
        self.assertEqual(board.turn, "white")

    def test_apply_uci_move_rejects_bad_coordinates(self):
        board = Board()
        mg = MoveGenerator(board)

        self.assertFalse(apply_uci_move(board, mg, "e2e9"))
        self.assertFalse(apply_uci_move(board, mg, "e2"))
        self.assertEqual(board.get_piece(6, 4), "P")
        self.assertEqual(board.turn, "white")

    def test_apply_uci_move_requires_exact_promotion_legality(self):
        board = Board()
        mg = MoveGenerator(board)

        self.assertFalse(apply_uci_move(board, mg, "e2e4q"))
        self.assertEqual(board.get_piece(6, 4), "P")
        self.assertEqual(board.turn, "white")

        promo_board = make_board(
            [
                [".", ".", ".", ".", "k", ".", ".", "."],
                ["P", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", ".", ".", ".", "."],
                [".", ".", ".", ".", "K", ".", ".", "."],
            ]
        )
        promo_mg = MoveGenerator(promo_board)

        self.assertFalse(apply_uci_move(promo_board, promo_mg, "a7a8"))
        self.assertEqual(promo_board.get_piece(1, 0), "P")
        self.assertEqual(promo_board.turn, "white")


class UciProtocolTests(unittest.TestCase):
    def test_go_runs_in_background_and_stop_finishes_bestmove(self):
        class SlowSearch:
            def __init__(self):
                self.stop_search = False
                self.last_completed_depth = 1
                self.node_count = 1
                self.seldepth = 1
                self.transposition_table = {}
                self.tt_max_entries = 1
                self.started = threading.Event()

            def find_best_move(self, *args, **kwargs):
                self.started.set()
                while not self.stop_search:
                    time.sleep(0.001)
                return ((6, 4), (4, 4), None), 0

        output = []
        engine = UciEngine(emit=output.append)
        engine.mg = SlowSearch()

        t0 = time.perf_counter()
        self.assertTrue(engine.handle_line("go infinite"))
        self.assertLess(time.perf_counter() - t0, 0.5)
        self.assertTrue(engine.mg.started.wait(0.5))
        self.assertTrue(engine.search_thread.is_alive())

        self.assertTrue(engine.handle_line("isready"))
        self.assertIn("readyok", output)

        self.assertTrue(engine.handle_line("stop"))
        engine.wait_for_search()

        self.assertIn("bestmove e2e4", output)


if __name__ == "__main__":
    unittest.main()
