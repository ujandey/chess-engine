class MoveGenerator:
    MATE_SCORE = 1000
    PIECE_VALUES = {
        "p": 1,
        "n": 3,
        "b": 3,
        "r": 5,
        "q": 9,
        "k": 0,
    }

    def __init__(self, board):
        self.board = board

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

    def is_square_attacked(self, row, col, by_white):
        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece(r, c)

                if piece == ".":
                    continue

                if by_white and not piece.isupper():
                    continue
                if not by_white and not piece.islower():
                    continue

                if self.piece_attacks_square(r, c, row, col):
                    return True

        return False

    def find_king(self, is_white):
        target = "K" if is_white else "k"

        for r in range(8):
            for c in range(8):
                if self.board.get_piece(r, c) == target:
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

    def evaluate_position(self, depth=0):
        game_status = self.get_game_status()
        side_to_move_is_white = self.board.turn == "white"

        if game_status["result"] == "checkmate":
            if side_to_move_is_white:
                return -self.MATE_SCORE + depth
            return self.MATE_SCORE - depth

        if game_status["is_over"]:
            return 0

        score = 0

        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece == ".":
                    continue

                value = self.PIECE_VALUES[piece.lower()]
                if piece.isupper():
                    score += value
                else:
                    score -= value

        return score

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
