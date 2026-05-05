import unittest

from engine.board import Board
from engine.move_generator import MoveGenerator
from engine.uci import move_to_uci

# Each entry: FEN to load, set of accepted best-first moves (UCI strings),
# and the iterative-deepening depth to search.  Positions are chosen so the
# correct answer is forced at the given depth and the search completes quickly.
TACTICS = [
    {
        "name": "back_rank_mate_in_1",
        "fen": "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
        # Ra8#: rook slides to a8, covering the entire back rank; black king
        # is boxed by its own pawns on f7/g7/h7.
        "best": {"a1a8"},
        "depth": 1,
    },
    {
        "name": "queen_mate_in_1",
        "fen": "k7/8/KQ6/8/8/8/8/8 w - - 0 1",
        # Three queen moves all give immediate checkmate: Qb8, Qa7, Qb7.
        "best": {"b6b8", "b6a7", "b6b7"},
        "depth": 1,
    },
    {
        "name": "rook_and_king_support_mate_in_1",
        "fen": "7k/5K2/6R1/8/8/8/8/8 w - - 0 1",
        # Rh6#: rook slides to h6, covering the h-file (h7, h8); white king
        # on f7 covers g7 and g8; all black king escapes are shut off.
        "best": {"g6h6"},
        "depth": 1,
    },
    {
        "name": "knight_fork_wins_rook",
        "fen": "8/3r4/2k5/8/8/5N2/8/R3K3 w - - 0 1",
        # Ne5+: knight forks the black king (c6) and black rook (d7).
        # After any king move white plays Nxd7, winning the rook cleanly.
        "best": {"f3e5"},
        "depth": 3,
    },
    {
        "name": "bishop_captures_pinned_knight",
        "fen": "8/8/4k3/8/2n5/8/B7/4K3 w - - 0 1",
        # Bishop on a2 absolutely pins the knight on c4 against the king on
        # e6 (all three are on the a2-e6 diagonal); Bxc4 wins the knight.
        "best": {"a2c4"},
        "depth": 1,
    },
    {
        "name": "rook_captures_and_delivers_back_rank_mate",
        "fen": "r5k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
        # Rxa8#: captures the black rook on a8 and simultaneously delivers
        # back-rank checkmate (same pattern as position 1 after recapture).
        "best": {"a1a8"},
        "depth": 1,
    },
    {
        "name": "pawn_promotes_to_queen",
        "fen": "8/6P1/6K1/8/8/8/8/7k w - - 0 1",
        # White pawn on g7 promotes to queen on g8; the black king on h1 is
        # far away and cannot stop it.  Queen promotion is a decisive material
        # gain - no other first move comes close.
        "best": {"g7g8q"},
        "depth": 1,
    },
]


def _run_tactic(tactic):
    board = Board()
    board.set_fen(tactic["fen"])
    mg = MoveGenerator(board)
    mg.in_opening = False
    is_white = board.turn == "white"
    move, _ = mg.find_best_move(tactic["depth"], is_white, verbose=False)
    return move_to_uci(move)


class TacticsTests(unittest.TestCase):

    def _assert_tactic(self, tactic):
        found = _run_tactic(tactic)
        self.assertIn(
            found,
            tactic["best"],
            msg=(
                f'{tactic["name"]}: expected one of '
                f'{sorted(tactic["best"])} but got {found!r}'
            ),
        )

    def test_back_rank_mate_in_1(self):
        self._assert_tactic(TACTICS[0])

    def test_queen_mate_in_1(self):
        self._assert_tactic(TACTICS[1])

    def test_rook_and_king_support_mate_in_1(self):
        self._assert_tactic(TACTICS[2])

    def test_knight_fork_wins_rook(self):
        self._assert_tactic(TACTICS[3])

    def test_bishop_captures_pinned_knight(self):
        self._assert_tactic(TACTICS[4])

    def test_rook_captures_and_delivers_back_rank_mate(self):
        self._assert_tactic(TACTICS[5])

    def test_pawn_promotes_to_queen(self):
        self._assert_tactic(TACTICS[6])


if __name__ == "__main__":
    unittest.main()
