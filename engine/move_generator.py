import time

from engine.opening_book import get_book_move


class SearchTimeout(Exception):
    pass


class MoveGenerator:
    MATE_SCORE = 1000
    CHECK_BONUS = 0.25
    _TT_EXACT = 0
    _TT_LOWER = 1  # failed high — score is a lower bound
    _TT_UPPER = 2  # failed low  — score is an upper bound

    # Evaluation constants
    _BISHOP_PAIR_BONUS = 0.30
    _ISOLATED_PENALTY  = 0.20   # per isolated pawn
    _DOUBLED_PENALTY   = 0.15   # per extra pawn on same file

    PIECE_VALUES = {
        "p": 1,
        "n": 3,
        "b": 3,
        "r": 5,
        "q": 9,
        "k": 0,
    }

    # Piece-square tables — white's perspective, row 0 = rank 8, row 7 = rank 1.
    # For black pieces mirror vertically: use PST[7-row][col].
    # Values are in pawn units (0.10 ≈ 10% of a pawn).
    _PAWN_PST = [
        [ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # rank 8 (promotion, never here)
        [ 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50],  # rank 7 — almost promoted
        [ 0.10, 0.10, 0.20, 0.30, 0.30, 0.20, 0.10, 0.10],  # rank 6
        [ 0.05, 0.05, 0.10, 0.25, 0.25, 0.10, 0.05, 0.05],  # rank 5
        [ 0.00, 0.00, 0.00, 0.20, 0.20, 0.00, 0.00, 0.00],  # rank 4 — central push
        [ 0.05,-0.05,-0.10, 0.00, 0.00,-0.10,-0.05, 0.05],  # rank 3
        [ 0.05, 0.10, 0.10,-0.20,-0.20, 0.10, 0.10, 0.05],  # rank 2 — starting rank
        [ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # rank 1 (never here)
    ]

    _KNIGHT_PST = [
        [-0.50,-0.40,-0.30,-0.30,-0.30,-0.30,-0.40,-0.50],
        [-0.40,-0.20, 0.00, 0.00, 0.00, 0.00,-0.20,-0.40],
        [-0.30, 0.00, 0.10, 0.15, 0.15, 0.10, 0.00,-0.30],
        [-0.30, 0.05, 0.15, 0.20, 0.20, 0.15, 0.05,-0.30],
        [-0.30, 0.00, 0.15, 0.20, 0.20, 0.15, 0.00,-0.30],
        [-0.30, 0.05, 0.10, 0.15, 0.15, 0.10, 0.05,-0.30],
        [-0.40,-0.20, 0.00, 0.05, 0.05, 0.00,-0.20,-0.40],
        [-0.50,-0.40,-0.30,-0.30,-0.30,-0.30,-0.40,-0.50],
    ]

    _BISHOP_PST = [
        [-0.20,-0.10,-0.10,-0.10,-0.10,-0.10,-0.10,-0.20],
        [-0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.10],
        [-0.10, 0.00, 0.05, 0.10, 0.10, 0.05, 0.00,-0.10],
        [-0.10, 0.05, 0.05, 0.10, 0.10, 0.05, 0.05,-0.10],
        [-0.10, 0.00, 0.10, 0.10, 0.10, 0.10, 0.00,-0.10],
        [-0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10,-0.10],
        [-0.10, 0.05, 0.00, 0.00, 0.00, 0.00, 0.05,-0.10],
        [-0.20,-0.10,-0.10,-0.10,-0.10,-0.10,-0.10,-0.20],
    ]

    # Row 1 = rank 7 for white — rook on 7th is a major endgame weapon
    _ROOK_PST = [
        [ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        [ 0.05, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.05],  # 7th rank bonus
        [-0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.05],
        [-0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.05],
        [-0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.05],
        [-0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.05],
        [-0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.05],
        [ 0.00, 0.00, 0.00, 0.05, 0.05, 0.00, 0.00, 0.00],
    ]

    _QUEEN_PST = [
        [-0.20,-0.10,-0.10,-0.05,-0.05,-0.10,-0.10,-0.20],
        [-0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,-0.10],
        [-0.10, 0.00, 0.05, 0.05, 0.05, 0.05, 0.00,-0.10],
        [-0.05, 0.00, 0.05, 0.05, 0.05, 0.05, 0.00,-0.05],
        [ 0.00, 0.00, 0.05, 0.05, 0.05, 0.05, 0.00,-0.05],
        [-0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.00,-0.10],
        [-0.10, 0.00, 0.05, 0.00, 0.00, 0.00, 0.00,-0.10],
        [-0.20,-0.10,-0.10,-0.05,-0.05,-0.10,-0.10,-0.20],
    ]

    # King prefers castled corner in the middlegame
    _KING_PST = [
        [-0.30,-0.40,-0.40,-0.50,-0.50,-0.40,-0.40,-0.30],
        [-0.30,-0.40,-0.40,-0.50,-0.50,-0.40,-0.40,-0.30],
        [-0.30,-0.40,-0.40,-0.50,-0.50,-0.40,-0.40,-0.30],
        [-0.30,-0.40,-0.40,-0.50,-0.50,-0.40,-0.40,-0.30],
        [-0.20,-0.30,-0.30,-0.40,-0.40,-0.30,-0.30,-0.20],
        [-0.10,-0.20,-0.20,-0.20,-0.20,-0.20,-0.20,-0.10],
        [ 0.20, 0.20, 0.00, 0.00, 0.00, 0.00, 0.20, 0.20],
        [ 0.20, 0.30, 0.10, 0.00, 0.00, 0.10, 0.30, 0.20],  # castled king corners
    ]

    PST = {
        "p": _PAWN_PST,
        "n": _KNIGHT_PST,
        "b": _BISHOP_PST,
        "r": _ROOK_PST,
        "q": _QUEEN_PST,
        "k": _KING_PST,
    }
    EVAL_TABLE = None

    def __init__(self, board):
        self.board = board
        self.board.refresh_zobrist_hash()
        self.transposition_table = {}
        self.killers = [[None, None] for _ in range(20)]
        self.history = {}
        self.nodes_searched = 0
        self.node_count = 0
        self.in_opening = True
        self.search_deadline = None
        self.stop_search = False
        self.last_completed_depth = 0
        self.last_search_time = 0.0
        self.seldepth = 0
        self._search_position_counts = {}
        self.tt_max_entries = 64 * 1024 * 1024 // 300  # ~224K entries (64 MB default)
        if MoveGenerator.EVAL_TABLE is None:
            MoveGenerator.EVAL_TABLE = self._build_eval_table()

    def set_hash_size(self, mb):
        self.tt_max_entries = max(1000, mb * 1024 * 1024 // 300)
        if len(self.transposition_table) > self.tt_max_entries:
            self.transposition_table.clear()

    @classmethod
    def _build_eval_table(cls):
        table = []
        for row in range(8):
            table.append([])
            for col in range(8):
                col_values = {".": 0}
                for piece_type, material in cls.PIECE_VALUES.items():
                    col_values[piece_type.upper()] = material + cls.PST[piece_type][row][col]
                    col_values[piece_type] = -(material + cls.PST[piece_type][7 - row][col])
                table[row].append(col_values)
        return table

    def piece_belongs_to_side(self, piece, is_white):
        if piece == ".":
            return False
        return piece.isupper() if is_white else piece.islower()

    def piece_belongs_to_current_player(self, piece):
        if self.board.turn == "white":
            return piece.isupper()
        return piece.islower()

    def get_piece_moves(self, row, col, ignore_turn=False):
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return []

        if not ignore_turn and not self.piece_belongs_to_current_player(piece):
            return []

        piece_type = piece.lower()

        if piece_type == "p":
            return self.generate_pawn_moves(row, col)
        if piece_type == "n":
            return self.generate_knight_moves(row, col)
        if piece_type == "b":
            return self.generate_bishop_moves(row, col)
        if piece_type == "r":
            return self.generate_rook_moves(row, col)
        if piece_type == "q":
            return self.generate_queen_moves(row, col)
        if piece_type == "k":
            return self.generate_king_moves(row, col)

        return []

    def is_inside_board(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8

    def is_opponent(self, piece, target):
        return (piece.isupper() and target.islower()) or (
            piece.islower() and target.isupper()
        )

    def generate_sliding_moves(self, row, col, directions):
        moves = []
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return moves

        for dr, dc in directions:
            next_row = row + dr
            next_col = col + dc

            while self.is_inside_board(next_row, next_col):
                target = self.board.get_piece(next_row, next_col)

                if target == ".":
                    moves.append((next_row, next_col))
                elif self.is_opponent(piece, target):
                    moves.append((next_row, next_col))
                    break
                else:
                    break

                next_row += dr
                next_col += dc

        return moves

    def get_pawn_attack_squares(self, row, col):
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return []

        direction = -1 if piece.isupper() else 1
        attacks = []

        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if self.is_inside_board(new_row, new_col):
                attacks.append((new_row, new_col))

        return attacks

    def get_king_attack_squares(self, row, col):
        moves = []

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                new_row = row + dr
                new_col = col + dc
                if self.is_inside_board(new_row, new_col):
                    moves.append((new_row, new_col))

        return moves

    def generate_pawn_moves(self, row, col):
        moves = []
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return moves

        direction = -1 if piece.isupper() else 1
        new_row = row + direction

        if self.is_inside_board(new_row, col) and self.board.get_piece(new_row, col) == ".":
            moves.append((new_row, col))

            start_row = 6 if piece.isupper() else 1
            if row == start_row:
                new_row_2 = row + 2 * direction
                if self.is_inside_board(new_row_2, col) and self.board.get_piece(new_row_2, col) == ".":
                    moves.append((new_row_2, col))

        for dc in [-1, 1]:
            new_col = col + dc
            if self.is_inside_board(new_row, new_col):
                target = self.board.get_piece(new_row, new_col)
                if target != "." and self.is_opponent(piece, target):
                    moves.append((new_row, new_col))
                elif self.board.en_passant_target == (new_row, new_col):
                    adjacent_piece = self.board.get_piece(row, new_col)
                    if adjacent_piece != "." and adjacent_piece.lower() == "p" and self.is_opponent(piece, adjacent_piece):
                        moves.append((new_row, new_col))

        return moves

    def generate_knight_moves(self, row, col):
        moves = []
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return moves

        knight_moves = [
            (-2, -1), (-2, 1),
            (-1, -2), (-1, 2),
            (1, -2), (1, 2),
            (2, -1), (2, 1),
        ]

        for dr, dc in knight_moves:
            new_row = row + dr
            new_col = col + dc

            if not self.is_inside_board(new_row, new_col):
                continue

            target = self.board.get_piece(new_row, new_col)
            if target == "." or self.is_opponent(piece, target):
                moves.append((new_row, new_col))

        return moves

    def generate_rook_moves(self, row, col):
        return self.generate_sliding_moves(row, col, [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ])

    def generate_bishop_moves(self, row, col):
        return self.generate_sliding_moves(row, col, [
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ])

    def generate_queen_moves(self, row, col):
        return self.generate_rook_moves(row, col) + self.generate_bishop_moves(row, col)

    def generate_king_moves(self, row, col):
        moves = []
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return moves

        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ]

        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc

            if not self.is_inside_board(new_row, new_col):
                continue

            target = self.board.get_piece(new_row, new_col)
            if target == "." or self.is_opponent(piece, target):
                moves.append((new_row, new_col))

        if piece.isupper():
            moves += self.get_castling_moves(row, col, True)
        else:
            moves += self.get_castling_moves(row, col, False)

        return moves

    def get_castling_moves(self, row, col, is_white):
        moves = []

        if self.is_in_check(is_white):
            return moves

        if is_white:
            r = 7

            if self.board.castling_rights["white_kingside"]:
                if (
                    self.board.get_piece(r, 7) == "R"
                    and self.board.get_piece(r, 5) == "."
                    and self.board.get_piece(r, 6) == "."
                    and not self.is_square_attacked(r, 5, by_white=False)
                    and not self.is_square_attacked(r, 6, by_white=False)
                ):
                    moves.append((r, 6))

            if self.board.castling_rights["white_queenside"]:
                if (
                    self.board.get_piece(r, 0) == "R"
                    and self.board.get_piece(r, 1) == "."
                    and self.board.get_piece(r, 2) == "."
                    and self.board.get_piece(r, 3) == "."
                    and not self.is_square_attacked(r, 2, by_white=False)
                    and not self.is_square_attacked(r, 3, by_white=False)
                ):
                    moves.append((r, 2))
        else:
            r = 0

            if self.board.castling_rights["black_kingside"]:
                if (
                    self.board.get_piece(r, 7) == "r"
                    and self.board.get_piece(r, 5) == "."
                    and self.board.get_piece(r, 6) == "."
                    and not self.is_square_attacked(r, 5, by_white=True)
                    and not self.is_square_attacked(r, 6, by_white=True)
                ):
                    moves.append((r, 6))

            if self.board.castling_rights["black_queenside"]:
                if (
                    self.board.get_piece(r, 0) == "r"
                    and self.board.get_piece(r, 1) == "."
                    and self.board.get_piece(r, 2) == "."
                    and self.board.get_piece(r, 3) == "."
                    and not self.is_square_attacked(r, 2, by_white=True)
                    and not self.is_square_attacked(r, 3, by_white=True)
                ):
                    moves.append((r, 2))

        return moves

    def piece_attacks_square(self, row, col, target_row, target_col):
        piece = self.board.get_piece(row, col)
        piece_type = piece.lower()

        if piece_type == "p":
            moves = self.get_pawn_attack_squares(row, col)
        elif piece_type == "k":
            moves = self.get_king_attack_squares(row, col)
        else:
            moves = self.get_piece_moves(row, col, ignore_turn=True)

        return (target_row, target_col) in moves

    def has_any_legal_moves(self, is_white):
        current_turn = self.board.turn
        self.board.turn = "white" if is_white else "black"

        try:
            for row in range(8):
                for col in range(8):
                    piece = self.board.get_piece(row, col)
                    if not self.piece_belongs_to_side(piece, is_white):
                        continue

                    if self.get_legal_moves(row, col):
                        return True
        finally:
            self.board.turn = current_turn

        return False

    def get_legal_moves(self, row, col):
        piece = self.board.get_piece(row, col)

        if piece == ".":
            return []

        is_white = piece.isupper()
        pseudo_moves = self.get_piece_moves(row, col)
        legal_moves = []

        for move in pseudo_moves:
            move_state = self.board.make_move((row, col), move)

            if not self.is_in_check(is_white):
                legal_moves.append(move)

            self.board.undo_move((row, col), move, move_state)

        return legal_moves

    def get_capture_moves(self, row, col):
        board = self.board.board
        piece = board[row][col]
        if piece == ".":
            return []

        moves = []
        is_white = piece.isupper()
        piece_type = piece.lower()

        if piece_type == "p":
            direction = -1 if is_white else 1
            target_row = row + direction
            if 0 <= target_row < 8:
                for dc in (-1, 1):
                    target_col = col + dc
                    if not 0 <= target_col < 8:
                        continue
                    target = board[target_row][target_col]
                    if target != "." and (target.islower() if is_white else target.isupper()):
                        moves.append((target_row, target_col))
                    elif self.board.en_passant_target == (target_row, target_col):
                        adjacent = board[row][target_col]
                        if adjacent.lower() == "p" and (adjacent.islower() if is_white else adjacent.isupper()):
                            moves.append((target_row, target_col))
            return moves

        if piece_type == "n":
            for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                           (1, -2), (1, 2), (2, -1), (2, 1)):
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    target = board[r][c]
                    if target != "." and (target.islower() if is_white else target.isupper()):
                        moves.append((r, c))
            return moves

        if piece_type == "k":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    r, c = row + dr, col + dc
                    if 0 <= r < 8 and 0 <= c < 8:
                        target = board[r][c]
                        if target != "." and (target.islower() if is_white else target.isupper()):
                            moves.append((r, c))
            return moves

        directions = []
        if piece_type in ("b", "q"):
            directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        if piece_type in ("r", "q"):
            directions += [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target != ".":
                    if target.islower() if is_white else target.isupper():
                        moves.append((r, c))
                    break
                r += dr
                c += dc

        return moves

    def generate_all_legal_moves(self, is_white):
        moves = []

        for r, c in self.board.iter_side_pieces(is_white):
            piece = self.board.get_piece(r, c)
            if piece == "." or piece.isupper() != is_white:
                self.board.refresh_zobrist_hash()
                return self.generate_all_legal_moves(is_white)

            is_pawn = piece.lower() == "p"
            for end in self.get_legal_moves(r, c):
                if is_pawn and end[0] in (0, 7):
                    for promo in ("Q", "R", "B", "N"):
                        moves.append(((r, c), end, promo))
                else:
                    moves.append(((r, c), end, None))

        return moves

    def perft(self, depth, is_white=None):
        if is_white is None:
            is_white = self.board.turn == "white"

        if depth == 0:
            return 1

        previous_turn = self.board.turn
        self.board.turn = "white" if is_white else "black"
        nodes = 0
        try:
            for start, end, promo in self.generate_all_legal_moves(is_white):
                move_state = self.board.make_move(start, end, promo)
                nodes += self.perft(depth - 1, not is_white)
                self.board.undo_move(start, end, move_state)
        finally:
            self.board.turn = previous_turn

        return nodes

    def perft_divide(self, depth, is_white=None):
        if is_white is None:
            is_white = self.board.turn == "white"

        previous_turn = self.board.turn
        self.board.turn = "white" if is_white else "black"
        results = []
        try:
            for start, end, promo in self.generate_all_legal_moves(is_white):
                move_state = self.board.make_move(start, end, promo)
                nodes = self.perft(depth - 1, not is_white)
                self.board.undo_move(start, end, move_state)
                results.append(((start, end, promo), nodes))
        finally:
            self.board.turn = previous_turn

        return results

    # ------------------------------------------------------------------
    # Move ordering
    # ------------------------------------------------------------------

    def is_capture_move(self, start, end):
        sr, sc = start
        er, ec = end
        piece = self.board.get_piece(sr, sc)
        target = self.board.get_piece(er, ec)
        return target != "." or (piece.lower() == "p" and sc != ec)

    def is_promotion_move(self, start, end):
        piece = self.board.get_piece(start[0], start[1])
        return piece.lower() == "p" and end[0] in (0, 7)

    def _can_null_move_prune(self, is_white):
        board = self.board.board
        side_non_pawn_material = 0
        total_non_king_material = 0

        for row in board:
            for piece in row:
                piece_type = piece.lower()
                if piece == "." or piece_type == "k":
                    continue

                value = self.PIECE_VALUES[piece_type]
                total_non_king_material += value
                if piece_type != "p" and is_white == piece.isupper():
                    side_non_pawn_material += value

        return side_non_pawn_material >= 7 and total_non_king_material >= 14

    def _move_order_score(self, start, end, promo=None, depth=0, tt_move=None):
        move = (start, end, promo)
        if move == tt_move:
            return 1_000_000

        score = 0
        sr, sc = start
        er, ec = end
        mover  = self.board.get_piece(sr, sc)
        target = self.board.get_piece(er, ec)

        if target != ".":
            victim_val   = self.PIECE_VALUES.get(target.lower(), 0)
            attacker_val = self.PIECE_VALUES.get(mover.lower(), 0)
            score += 100_000 + 100 * victim_val - attacker_val
        elif mover.lower() == "p" and sc != ec:
            score += 100_000 + 100
        elif 0 <= depth < len(self.killers):
            if move == self.killers[depth][0]:
                score += 80_000
            elif move == self.killers[depth][1]:
                score += 70_000

        if score < 70_000:
            score += self.history.get(move, 0)

        if mover.lower() == "p" and (er == 0 or er == 7):
            promo_bonus = {"Q": 90_000, "N": 87_000, "R": 50_000, "B": 48_000}
            score += promo_bonus.get(promo, 90_000)

        return score

    def _store_killer(self, depth, move):
        if depth < len(self.killers) and move != self.killers[depth][0]:
            self.killers[depth][1] = self.killers[depth][0]
            self.killers[depth][0] = move

    def _store_history(self, depth, move):
        self.history[move] = self.history.get(move, 0) + depth * depth

    def order_moves(self, moves, is_white, depth=0, tt_move=None):
        return sorted(
            moves,
            key=lambda m: self._move_order_score(m[0], m[1], m[2], depth, tt_move),
            reverse=True,
        )

    def _check_search_timeout(self):
        if self.stop_search:
            raise SearchTimeout()
        if self.search_deadline is not None and time.perf_counter() >= self.search_deadline:
            raise SearchTimeout()

    def _extract_pv(self, is_white_turn, max_depth, first_move=None):
        """Walk TT from current position to build a PV line.

        first_move: the root best move (not stored in TT by the root loop).
        """
        pv = []
        states = []
        seen = set()
        cur_white = is_white_turn
        orig_turn = self.board.turn
        remaining = max_depth
        try:
            if first_move is not None and remaining > 0:
                start, end, promo = first_move
                self.board.turn = "white" if cur_white else "black"
                state = self.board.make_move(start, end, promo)
                states.append((start, end, state))
                pv.append(first_move)
                cur_white = not cur_white
                remaining -= 1

            for _ in range(remaining):
                key = self.board.zobrist_hash
                if key in seen:
                    break
                seen.add(key)
                entry = self.transposition_table.get(key)
                if entry is None or entry[3] is None:
                    break
                move = entry[3]
                start, end, promo = move
                self.board.turn = "white" if cur_white else "black"
                state = self.board.make_move(start, end, promo)
                states.append((start, end, state))
                pv.append(move)
                cur_white = not cur_white
        except (IndexError, KeyError, TypeError, ValueError):
            pass
        finally:
            for s, e, st in reversed(states):
                self.board.undo_move(s, e, st)
            self.board.turn = orig_turn
        return pv

    def _side_multiplier(self, is_white_turn):
        return 1 if is_white_turn else -1

    def _evaluate_for_side(self, is_white_turn):
        return self._evaluate_material() * self._side_multiplier(is_white_turn)

    def static_exchange_eval(self, start, end):
        sr, sc = start
        er, ec = end
        mover = self.board.get_piece(sr, sc)
        target = self.board.get_piece(er, ec)

        if target == "." and not (mover.lower() == "p" and sc != ec):
            return 0.0

        victim_value = self.PIECE_VALUES.get(target.lower(), 1 if target == "." else 0)
        attacker_value = self.PIECE_VALUES.get(mover.lower(), 0)
        gain = victim_value - attacker_value

        move_state = self.board.make_move(start, end)
        try:
            occupied_by_white = mover.isupper()
            if self.is_square_attacked(er, ec, by_white=not occupied_by_white):
                cheapest_recapture = 9
                for r, c in self.board.iter_side_pieces(not occupied_by_white):
                    piece = self.board.get_piece(r, c)
                    if piece != "." and self.piece_attacks_square(r, c, er, ec):
                        cheapest_recapture = min(
                            cheapest_recapture,
                            self.PIECE_VALUES.get(piece.lower(), 0),
                        )
                gain -= min(attacker_value, cheapest_recapture)
        finally:
            self.board.undo_move(start, end, move_state)

        return gain

    def quiescence(self, alpha, beta, is_white_turn, ply=0):
        self.nodes_searched += 1
        self.node_count += 1
        if ply > self.seldepth:
            self.seldepth = ply
        if (self.node_count & 2047) == 0:
            self._check_search_timeout()

        previous_turn = self.board.turn
        self.board.turn = "white" if is_white_turn else "black"

        try:
            stand_pat = self._evaluate_for_side(is_white_turn)
            if stand_pat >= beta:
                return beta
            best = stand_pat
            if best > alpha:
                alpha = best

            captures = []
            for r, c in self.board.iter_side_pieces(is_white_turn):
                piece = self.board.get_piece(r, c)
                if piece == "." or piece.isupper() != is_white_turn:
                    continue
                is_pawn = piece.lower() == "p"
                for end in self.get_capture_moves(r, c):
                    if is_pawn and end[0] in (0, 7):
                        for promo in ("Q", "R", "B", "N"):
                            captures.append(((r, c), end, promo))
                    else:
                        captures.append(((r, c), end, None))

            captures = self.order_moves(captures, is_white_turn)

            for start, end, promo in captures:
                if not self.is_promotion_move(start, end) and self.static_exchange_eval(start, end) < -0.20:
                    continue

                move_state = self.board.make_move(start, end, promo)
                if self.is_in_check(is_white_turn):
                    self.board.undo_move(start, end, move_state)
                    continue
                score = -self.quiescence(-beta, -alpha, not is_white_turn, ply + 1)
                self.board.undo_move(start, end, move_state)
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
        finally:
            self.board.turn = previous_turn

        return best

    def minimax(self, depth, is_white_turn, alpha=float("-inf"), beta=float("inf")):
        score = self.negamax(depth, is_white_turn, alpha, beta)
        return score if is_white_turn else -score

    def negamax(self, depth, is_white_turn, alpha=float("-inf"), beta=float("inf"), allow_null=True, ply=0):
        self.nodes_searched += 1
        self.node_count += 1
        if (self.node_count & 2047) == 0:
            self._check_search_timeout()

        if self.board.halfmove_clock >= 100:
            return 0

        previous_turn = self.board.turn
        self.board.turn = "white" if is_white_turn else "black"
        search_key = None
        counted_search_key = False

        try:
            in_check = self.is_in_check(is_white_turn)
            if in_check:
                depth += 1

            alpha_orig = alpha
            beta_orig = beta
            tt_key = self.board.zobrist_hash
            search_key = tt_key

            repetition_count = (
                self.board.position_counts.get(tt_key, 0)
                + self._search_position_counts.get(tt_key, 0)
            )
            if repetition_count + 1 >= 3:
                return 0
            self._search_position_counts[tt_key] = self._search_position_counts.get(tt_key, 0) + 1
            counted_search_key = True

            tt_entry = self.transposition_table.get(tt_key)
            tt_move = tt_entry[3] if tt_entry is not None and len(tt_entry) > 3 else None
            if tt_entry is not None and tt_entry[0] >= depth:
                _, tt_score, flag = tt_entry[:3]
                if flag == self._TT_EXACT:
                    return tt_score
                if flag == self._TT_LOWER:
                    alpha = max(alpha, tt_score)
                else:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

            if depth == 0 and not in_check:
                return self.quiescence(alpha, beta, is_white_turn, ply + 1)

            if (
                allow_null
                and depth >= 3
                and not in_check
                and self._can_null_move_prune(is_white_turn)
            ):
                previous_ep = self.board.en_passant_target
                self.board.en_passant_target = None
                try:
                    # Clamp beta so -beta+1 stays finite (float("-inf")+1 == -inf in Python)
                    null_beta = min(beta, self.MATE_SCORE + depth + 1)
                    null_score = -self.negamax(depth - 3, not is_white_turn, -null_beta, -null_beta + 1, False, ply + 1)
                finally:
                    self.board.en_passant_target = previous_ep

                if null_score >= beta:
                    return beta

            moves = self.generate_all_legal_moves(is_white_turn)
            if not moves:
                if in_check:
                    return -self.MATE_SCORE + ply
                return 0

            moves = self.order_moves(moves, is_white_turn, depth, tt_move)

            best_score = float("-inf")
            best_move_local = None
            for move_index, (start, end, promo) in enumerate(moves):
                target = self.board.get_piece(end[0], end[1])
                mover = self.board.get_piece(start[0], start[1])
                is_capture = target != "." or (mover.lower() == "p" and start[1] != end[1])
                is_promotion = self.is_promotion_move(start, end)

                move_state = self.board.make_move(start, end, promo)
                gives_check = False
                if move_index > 5 and depth >= 3 and not is_capture and not is_promotion:
                    gives_check = self.is_in_check(not is_white_turn)

                next_depth = depth - 1
                reduced = False
                if move_index > 5 and depth >= 3 and not is_capture and not is_promotion and not gives_check:
                    next_depth = depth - 2
                    reduced = True

                if move_index == 0:
                    score = -self.negamax(next_depth, not is_white_turn, -beta, -alpha, ply=ply + 1)
                else:
                    score = -self.negamax(next_depth, not is_white_turn, -alpha - 1, -alpha, ply=ply + 1)
                    if score > alpha and score < beta:
                        score = -self.negamax(depth - 1, not is_white_turn, -beta, -alpha, ply=ply + 1)

                if reduced and score > alpha:
                    score = -self.negamax(depth - 1, not is_white_turn, -beta, -alpha, ply=ply + 1)

                self.board.undo_move(start, end, move_state)
                if score > best_score:
                    best_score = score
                    best_move_local = (start, end, promo)
                if best_score > alpha:
                    alpha = best_score
                if alpha >= beta:
                    if not is_capture:
                        self._store_killer(depth, (start, end, promo))
                        self._store_history(depth, (start, end, promo))
                    break

            if abs(best_score) < self.MATE_SCORE - 10:
                if best_score <= alpha_orig:
                    flag = self._TT_UPPER
                elif best_score >= beta_orig:
                    flag = self._TT_LOWER
                else:
                    flag = self._TT_EXACT
                if len(self.transposition_table) < self.tt_max_entries:
                    self.transposition_table[tt_key] = (depth, best_score, flag, best_move_local)
        finally:
            if counted_search_key and search_key is not None:
                count = self._search_position_counts.get(search_key, 0)
                if count <= 1:
                    self._search_position_counts.pop(search_key, None)
                else:
                    self._search_position_counts[search_key] = count - 1
            self.board.turn = previous_turn

        return best_score

    def find_best_move(self, depth, is_white_turn, max_time=None, verbose=True, on_depth_complete=None):
        previous_turn = self.board.turn
        self.board.turn = "white" if is_white_turn else "black"

        try:
            if self.in_opening:
                book_move = get_book_move(self.board)
                if book_move is not None:
                    start, end = book_move
                    if end in self.get_legal_moves(start[0], start[1]):
                        piece = self.board.get_piece(start[0], start[1])
                        promo = "Q" if piece.lower() == "p" and end[0] in (0, 7) else None
                        return (start, end, promo), self.evaluate_position()
                self.in_opening = False

            moves = self.generate_all_legal_moves(is_white_turn)
        finally:
            self.board.turn = previous_turn

        if not moves:
            return None, self.evaluate_position()

        moves = self.order_moves(moves, is_white_turn)
        best_move = moves[0]
        best_score = float("-inf")

        t0 = time.perf_counter()
        self.nodes_searched = 0
        self.node_count = 0
        self.last_completed_depth = 0
        self.search_deadline = (t0 + max_time) if max_time is not None else None
        self.stop_search = False
        self._search_position_counts = {}

        try:
            for current_depth in range(1, depth + 1):
                depth_t0 = time.perf_counter()
                depth_nodes_before = self.nodes_searched
                self.seldepth = 0
                moves.sort(key=lambda m: 0 if m == best_move else 1)

                iter_best_move = None
                iter_best_score = float("-inf")
                alpha = float("-inf")
                beta = float("inf")

                for move_index, (start, end, promo) in enumerate(moves):
                    self.board.turn = "white" if is_white_turn else "black"
                    move_state = self.board.make_move(start, end, promo)
                    if move_index == 0:
                        score = -self.negamax(current_depth - 1, not is_white_turn, -beta, -alpha, ply=1)
                    else:
                        score = -self.negamax(current_depth - 1, not is_white_turn, -alpha - 1, -alpha, ply=1)
                        if score > alpha and score < beta:
                            score = -self.negamax(current_depth - 1, not is_white_turn, -beta, -alpha, ply=1)
                    self.board.undo_move(start, end, move_state)

                    if score > iter_best_score:
                        iter_best_score = score
                        iter_best_move = (start, end, promo)
                    if iter_best_score > alpha:
                        alpha = iter_best_score

                if iter_best_move is not None:
                    best_move = iter_best_move
                    best_score = iter_best_score
                    self.last_completed_depth = current_depth

                dt = time.perf_counter() - depth_t0
                depth_nodes = self.nodes_searched - depth_nodes_before
                nps = int(depth_nodes / dt) if dt > 0 else 0
                if verbose:
                    score_for_display = best_score if is_white_turn else -best_score
                    print(f"depth={current_depth:2d}  nodes={depth_nodes:>8,}  "
                          f"time={dt:.3f}s  NPS={nps:>8,}  score={score_for_display:.3f}")
                if on_depth_complete is not None:
                    pv = self._extract_pv(is_white_turn, current_depth, first_move=best_move)
                    on_depth_complete(current_depth, best_score, pv)
        except SearchTimeout:
            pass
        finally:
            self.board.turn = previous_turn
            self.search_deadline = None

        total_t = time.perf_counter() - t0
        self.last_search_time = total_t
        total_nps = int(self.node_count / total_t) if total_t > 0 else 0
        if verbose:
            print(f"--- total nodes={self.node_count:,}  time={total_t:.3f}s  NPS={total_nps:,} ---")
            print(f"Nodes: {self.node_count}")
            print(f"Time: {total_t:.3f} seconds")
            print(f"NPS: {total_nps}")

        return best_move, best_score if is_white_turn else -best_score

    def is_square_attacked(self, row, col, by_white):
        """
        Reverse-ray attack detection: cast rays FROM the target square outward.
        ~10-20x faster than the old approach of scanning all 64 squares and
        generating each piece's full move list.
        """
        b = self.board.board

        # --- Knight attacks ---
        for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                p = b[r][c]
                if (by_white and p == 'N') or (not by_white and p == 'n'):
                    return True

        # --- Pawn attacks (look in the direction pawns come FROM) ---
        # White pawns attack upward (row decreases), so a white pawn threatening
        # (row,col) sits one rank below: row+1.
        pawn_dir = 1 if by_white else -1
        for dc in (-1, 1):
            r, c = row + pawn_dir, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                p = b[r][c]
                if (by_white and p == 'P') or (not by_white and p == 'p'):
                    return True

        # --- King attacks ---
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    p = b[r][c]
                    if (by_white and p == 'K') or (not by_white and p == 'k'):
                        return True

        # --- Rook / Queen rays (horizontal & vertical) ---
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                p = b[r][c]
                if p != '.':
                    if by_white and p in ('R','Q'):
                        return True
                    if not by_white and p in ('r','q'):
                        return True
                    break
                r, c = r + dr, c + dc

        # --- Bishop / Queen rays (diagonal) ---
        for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                p = b[r][c]
                if p != '.':
                    if by_white and p in ('B','Q'):
                        return True
                    if not by_white and p in ('b','q'):
                        return True
                    break
                r, c = r + dr, c + dc

        return False

    def find_king(self, is_white):
        # O(1) in the search (make_move/undo_move keep the cache current).
        # Falls back to an O(64) scan when the board was assigned directly (e.g. in
        # tests) so the cached position no longer matches the actual board state.
        king_char = 'K' if is_white else 'k'
        pos = self.board.white_king_pos if is_white else self.board.black_king_pos
        if pos is not None and self.board.board[pos[0]][pos[1]] == king_char:
            return pos
        for r in range(8):
            for c in range(8):
                if self.board.board[r][c] == king_char:
                    return (r, c)
        return None

    def is_in_check(self, is_white):
        king_pos = self.find_king(is_white)

        if king_pos is None:
            return False

        return self.is_square_attacked(
            king_pos[0],
            king_pos[1],
            by_white=not is_white
        )

    def is_checkmate(self, is_white):
        return self.is_in_check(is_white) and not self.has_any_legal_moves(is_white)

    def is_stalemate(self, is_white):
        return not self.is_in_check(is_white) and not self.has_any_legal_moves(is_white)

    def is_insufficient_material(self):
        white_bishop_squares = []
        black_bishop_squares = []
        white_knights = 0
        black_knights = 0
        other_material = []

        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece in (".", "K", "k"):
                    continue

                piece_type = piece.lower()
                if piece_type == "b":
                    square_color = (row + col) % 2
                    if piece.isupper():
                        white_bishop_squares.append(square_color)
                    else:
                        black_bishop_squares.append(square_color)
                elif piece_type == "n":
                    if piece.isupper():
                        white_knights += 1
                    else:
                        black_knights += 1
                else:
                    other_material.append(piece)

        if other_material:
            return False

        white_minors = len(white_bishop_squares) + white_knights
        black_minors = len(black_bishop_squares) + black_knights
        total_minors = white_minors + black_minors

        if total_minors == 0:
            return True

        if total_minors == 1:
            return True

        if white_knights == 1 and black_knights == 1 and total_minors == 2:
            return True

        if (
            white_knights == 0
            and black_knights == 0
            and len(white_bishop_squares) == 1
            and len(black_bishop_squares) == 1
            and white_bishop_squares[0] == black_bishop_squares[0]
        ):
            return True

        return False

    def is_fifty_move_draw(self):
        return self.board.halfmove_clock >= 100

    def is_threefold_repetition(self):
        return self.board.position_counts.get(self.board.get_position_key(), 0) >= 3

    # Passed pawn bonuses indexed by advancement rank (0 = home, 6 = one step from promotion).
    # White rank = 7 - row (row 6 → rank 1 start, row 1 → rank 6 near promo).
    # Black rank = row   (row 1 → rank 1 start, row 6 → rank 6 near promo).
    _PASSED_BONUS = [0.0, 0.10, 0.15, 0.20, 0.30, 0.45, 0.65, 0.0]

    _ROOK_OPEN_FILE  = 0.20   # rook on a file with no pawns of either colour
    _ROOK_SEMI_OPEN  = 0.10   # rook on a file clear of friendly pawns only

    # King safety (all scaled by middlegame fraction so they fade to zero in endgames)
    _PAWN_SHIELD_BONUS = 0.15   # per pawn present in the king's two-rank shield zone
    _OPEN_FILE_PENALTY = 0.25   # shield file is fully open (no pawns either side)
    _SEMI_OPEN_PENALTY = 0.15   # shield file has enemy pawns but no friendly ones
    _MOBILITY_WEIGHTS = {"n": 0.015, "b": 0.012, "r": 0.008, "q": 0.004}
    _KING_PRESSURE_WEIGHTS = {"n": 0.08, "b": 0.07, "r": 0.10, "q": 0.16}
    _ENDGAME_KING_ACTIVITY = 0.08

    def _evaluate_material(self):
        """
        Hot-path evaluation used by quiescence stand_pat and evaluate_position.
        Single O(64) board scan accumulates:
          - material + PST via precomputed EVAL_TABLE
          - bishop counts for bishop pair bonus
          - pawn file maps {col: [rows]} for structure, passed pawns, rooks, king safety
          - non-pawn material totals for game-phase detection
        """
        score = 0
        board = self.board.board
        eval_table = self.EVAL_TABLE

        white_bishops = 0
        black_bishops = 0
        wpf = {}   # col -> [rows] of white pawns on that file
        bpf = {}   # col -> [rows] of black pawns on that file
        wnpm = 0   # white non-pawn material in pawn units
        bnpm = 0

        for row in range(8):
            row_data = board[row]
            row_table = eval_table[row]
            for col in range(8):
                piece = row_data[col]
                score += row_table[col][piece]
                if piece == 'B':
                    white_bishops += 1
                    wnpm += 3
                elif piece == 'b':
                    black_bishops += 1
                    bnpm += 3
                elif piece == 'P':
                    wpf.setdefault(col, []).append(row)
                elif piece == 'p':
                    bpf.setdefault(col, []).append(row)
                elif piece == 'N':
                    wnpm += 3
                elif piece == 'n':
                    bnpm += 3
                elif piece == 'R':
                    wnpm += 5
                elif piece == 'r':
                    bnpm += 5
                elif piece == 'Q':
                    wnpm += 9
                elif piece == 'q':
                    bnpm += 9

        # Bishop pair bonus
        if white_bishops >= 2:
            score += self._BISHOP_PAIR_BONUS
        if black_bishops >= 2:
            score -= self._BISHOP_PAIR_BONUS

        score += self._evaluate_pawn_structure(wpf, bpf)
        score += self._evaluate_passed_pawns(wpf, bpf)
        score += self._evaluate_rooks(wpf, bpf)

        phase = self._game_phase(wnpm, bnpm)
        score += self._evaluate_mobility()
        score += self._evaluate_endgame_king_activity(phase)
        if phase < 0.95:
            score += self._evaluate_king_safety(wpf, bpf, phase)
            score += self._evaluate_king_pressure(phase)

        return score

    # ------------------------------------------------------------------
    # Positional evaluation helpers (all called from _evaluate_material)
    # ------------------------------------------------------------------

    def _game_phase(self, wnpm, bnpm):
        """
        Phase fraction: 0.0 = full middlegame, 1.0 = full endgame.
        Smooth linear blend — avoids eval cliffs at phase transitions.
        Game-start npm ≈ 60; pure-endgame threshold ≈ 10.
        """
        return max(0.0, min(1.0, 1.0 - (wnpm + bnpm - 10.0) / 50.0))

    def _evaluate_pawn_structure(self, wpf, bpf):
        """
        Isolated and doubled pawn penalties. Returns White-perspective score.
        wpf/bpf: {col: [rows]} built in _evaluate_material.
        """
        score = 0.0
        ip = self._ISOLATED_PENALTY
        dp = self._DOUBLED_PENALTY

        for col, rows in wpf.items():
            cnt = len(rows)
            if (col - 1) not in wpf and (col + 1) not in wpf:
                score -= ip * cnt
            if cnt > 1:
                score -= dp * (cnt - 1)

        for col, rows in bpf.items():
            cnt = len(rows)
            if (col - 1) not in bpf and (col + 1) not in bpf:
                score += ip * cnt
            if cnt > 1:
                score += dp * (cnt - 1)

        return score

    def _evaluate_passed_pawns(self, wpf, bpf):
        """
        Bonus for pawns with no enemy pawn blocking or guarding ahead on same/adjacent files.
        White pawns advance toward row 0; black toward row 7.
        Rank index convention: white rank = 7-row, black rank = row
          (both give index 1 at starting rank, 6 near promotion).
        Returns White-perspective score.
        """
        score = 0.0
        bonus = self._PASSED_BONUS

        for col, rows in wpf.items():
            for row in rows:
                passed = True
                for r in range(row - 1, -1, -1):
                    for dc in (-1, 0, 1):
                        c2 = col + dc
                        if 0 <= c2 < 8 and c2 in bpf and r in bpf[c2]:
                            passed = False
                            break
                    if not passed:
                        break
                if passed:
                    score += bonus[7 - row]

        for col, rows in bpf.items():
            for row in rows:
                passed = True
                for r in range(row + 1, 8):
                    for dc in (-1, 0, 1):
                        c2 = col + dc
                        if 0 <= c2 < 8 and c2 in wpf and r in wpf[c2]:
                            passed = False
                            break
                    if not passed:
                        break
                if passed:
                    score -= bonus[row]

        return score

    def _evaluate_rooks(self, wpf, bpf):
        """
        Bonus for rooks on open or semi-open files.
        Complements the rook PST (which rewards rank but not file openness).
        Returns White-perspective score.
        """
        score = 0.0
        board = self.board.board
        ob = self._ROOK_OPEN_FILE
        sb = self._ROOK_SEMI_OPEN

        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece == 'R':
                    if col not in wpf and col not in bpf:
                        score += ob
                    elif col not in wpf:
                        score += sb
                elif piece == 'r':
                    if col not in wpf and col not in bpf:
                        score -= ob
                    elif col not in bpf:
                        score -= sb

        return score

    def _evaluate_mobility(self):
        score = 0.0
        board = self.board.board
        weights = self._MOBILITY_WEIGHTS
        previous_turn = self.board.turn

        try:
            for row in range(8):
                for col in range(8):
                    piece = board[row][col]
                    piece_type = piece.lower()
                    if piece_type not in weights:
                        continue
                    self.board.turn = "white" if piece.isupper() else "black"
                    mobility = len(self.get_piece_moves(row, col, ignore_turn=True))
                    bonus = weights[piece_type] * mobility
                    score += bonus if piece.isupper() else -bonus
        finally:
            self.board.turn = previous_turn

        return score

    def _evaluate_endgame_king_activity(self, phase):
        if phase <= 0:
            return 0.0

        def centrality(pos):
            row, col = pos
            return 3.5 - (abs(row - 3.5) + abs(col - 3.5)) / 2.0

        return (
            centrality(self.board.white_king_pos)
            - centrality(self.board.black_king_pos)
        ) * self._ENDGAME_KING_ACTIVITY * phase

    def _evaluate_king_pressure(self, phase):
        mg = 1.0 - phase
        if mg <= 0:
            return 0.0

        score = 0.0
        white_king = self.board.white_king_pos
        black_king = self.board.black_king_pos

        def near_king(square, king_pos):
            return abs(square[0] - king_pos[0]) <= 1 and abs(square[1] - king_pos[1]) <= 1

        previous_turn = self.board.turn
        try:
            for row in range(8):
                for col in range(8):
                    piece = self.board.board[row][col]
                    piece_type = piece.lower()
                    if piece_type not in self._KING_PRESSURE_WEIGHTS:
                        continue
                    self.board.turn = "white" if piece.isupper() else "black"
                    target_king = black_king if piece.isupper() else white_king
                    attacks = self.get_piece_moves(row, col, ignore_turn=True)
                    attacked_zone = sum(1 for square in attacks if near_king(square, target_king))
                    pressure = attacked_zone * self._KING_PRESSURE_WEIGHTS[piece_type] * mg
                    score += pressure if piece.isupper() else -pressure
        finally:
            self.board.turn = previous_turn

        return score

    def _evaluate_king_safety(self, wpf, bpf, phase):
        """
        Pawn-shield + open-file penalties for the king, scaled by middlegame fraction.
        Uses cached king positions (O(1)) and pawn file maps from the main scan.
        Known limitation: does not model enemy piece attack pressure — only pawn shield.
        """
        mg = 1.0 - phase   # 1.0 in pure middlegame, 0.0 in pure endgame
        shield_b = self._PAWN_SHIELD_BONUS * mg
        open_p   = self._OPEN_FILE_PENALTY * mg
        semi_p   = self._SEMI_OPEN_PENALTY * mg
        board = self.board.board
        score = 0.0

        def side_score(kr, kc, f_pawn, f_files, e_files, direction):
            s = 0.0
            sr1 = kr + direction
            sr2 = kr + 2 * direction
            for dc in (-1, 0, 1):
                c2 = kc + dc
                if not (0 <= c2 < 8):
                    continue
                has_shield = (
                    (0 <= sr1 < 8 and board[sr1][c2] == f_pawn) or
                    (0 <= sr2 < 8 and board[sr2][c2] == f_pawn)
                )
                if has_shield:
                    s += shield_b
                else:
                    f_here = c2 in f_files
                    e_here = c2 in e_files
                    if not f_here and not e_here:
                        s -= open_p
                    elif not f_here:
                        s -= semi_p
            return s

        wkr, wkc = self.board.white_king_pos
        bkr, bkc = self.board.black_king_pos
        # White king shields are on rows with LOWER index (toward rank 8), direction = -1
        score += side_score(wkr, wkc, 'P', wpf, bpf, -1)
        # Black king shields are on rows with HIGHER index (toward rank 1), direction = +1
        score -= side_score(bkr, bkc, 'p', bpf, wpf, +1)

        return score

    def evaluate_position(self, depth=0):
        side_to_move_is_white = self.board.turn == "white"

        if self.is_checkmate(side_to_move_is_white):
            if side_to_move_is_white:
                return -self.MATE_SCORE + depth
            return self.MATE_SCORE - depth

        if (
            self.is_stalemate(side_to_move_is_white)
            or self.is_fifty_move_draw()
            or self.is_threefold_repetition()
            or self.is_insufficient_material()
        ):
            return 0

        return self._evaluate_material()

    def get_game_status(self):
        side_to_move_is_white = self.board.turn == "white"
        side_name = "White" if side_to_move_is_white else "Black"
        winner = "Black" if side_to_move_is_white else "White"

        if self.is_checkmate(side_to_move_is_white):
            return {
                "is_over": True,
                "result": "checkmate",
                "message": f"Checkmate - {winner} wins",
            }

        if self.is_stalemate(side_to_move_is_white):
            return {
                "is_over": True,
                "result": "stalemate",
                "message": "Draw by stalemate",
            }

        if self.is_fifty_move_draw():
            return {
                "is_over": True,
                "result": "fifty_move_rule",
                "message": "Draw by 50-move rule",
            }

        if self.is_threefold_repetition():
            return {
                "is_over": True,
                "result": "threefold_repetition",
                "message": "Draw by threefold repetition",
            }

        if self.is_insufficient_material():
            return {
                "is_over": True,
                "result": "insufficient_material",
                "message": "Draw by insufficient material",
            }

        if self.is_in_check(side_to_move_is_white):
            return {
                "is_over": False,
                "result": "check",
                "message": f"{side_name} to move - in check",
            }

        return {
            "is_over": False,
            "result": "ongoing",
            "message": f"{side_name} to move",
        }
