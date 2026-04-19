class MoveGenerator:
    def __init__(self, board):
        self.board = board

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
