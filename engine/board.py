class Board:
    def __init__(self):
        self.board = self.create_starting_position()
        self.turn = "white"
        self.en_passant_target = None
        self.castling_rights = {
            "white_kingside": True,
            "white_queenside": True,
            "black_kingside": True,
            "black_queenside": True,
        }

    def create_starting_position(self):
        return [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"],
        ]

    def print_board(self):
        print("\n  a b c d e f g h")
        for i, row in enumerate(self.board):
            print(8 - i, " ".join(row), 8 - i)
        print("  a b c d e f g h\n")

    def get_piece(self, row, col):
        return self.board[row][col]

    def get_promotion_piece(self, piece, promotion_choice=None):
        if promotion_choice is None:
            return "Q" if piece.isupper() else "q"

        normalized_choice = promotion_choice.upper()
        if normalized_choice not in {"Q", "R", "B", "N"}:
            normalized_choice = "Q"

        return normalized_choice if piece.isupper() else normalized_choice.lower()

    def move_piece(self, start, end, promotion_choice=None):
        self.make_move(start, end, promotion_choice)
        self.turn = "black" if self.turn == "white" else "white"

    def update_castling_rights_for_rook(self, piece, row, col):
        if piece == "R":
            if (row, col) == (7, 0):
                self.castling_rights["white_queenside"] = False
            elif (row, col) == (7, 7):
                self.castling_rights["white_kingside"] = False
        elif piece == "r":
            if (row, col) == (0, 0):
                self.castling_rights["black_queenside"] = False
            elif (row, col) == (0, 7):
                self.castling_rights["black_kingside"] = False

    def make_move(self, start, end, promotion_choice=None):
        sr, sc = start
        er, ec = end

        piece = self.board[sr][sc]
        captured = self.board[er][ec]
        previous_castling_rights = self.castling_rights.copy()
        previous_en_passant_target = self.en_passant_target
        rook_move = None
        en_passant_capture = None
        promoted_from = None

        if piece == "K":
            self.castling_rights["white_kingside"] = False
            self.castling_rights["white_queenside"] = False
        elif piece == "k":
            self.castling_rights["black_kingside"] = False
            self.castling_rights["black_queenside"] = False

        self.update_castling_rights_for_rook(piece, sr, sc)
        self.update_castling_rights_for_rook(captured, er, ec)

        self.en_passant_target = None

        is_en_passant = (
            piece.lower() == "p"
            and ec != sc
            and captured == "."
            and previous_en_passant_target == (er, ec)
        )
        if is_en_passant:
            capture_row = sr
            captured = self.board[capture_row][ec]
            self.board[capture_row][ec] = "."
            en_passant_capture = ((capture_row, ec), captured)

        self.board[sr][sc] = "."
        self.board[er][ec] = piece

        if piece == "P" and er == 0:
            self.board[er][ec] = self.get_promotion_piece(piece, promotion_choice)
            promoted_from = "P"
        elif piece == "p" and er == 7:
            self.board[er][ec] = self.get_promotion_piece(piece, promotion_choice)
            promoted_from = "p"

        if piece.lower() == "p" and abs(er - sr) == 2:
            self.en_passant_target = ((sr + er) // 2, sc)

        is_castle = piece in ("K", "k") and abs(ec - sc) == 2
        if is_castle:
            rook_start_col = 7 if ec > sc else 0
            rook_end_col = 5 if ec > sc else 3
            rook_piece = self.board[er][rook_start_col]
            self.board[er][rook_start_col] = "."
            self.board[er][rook_end_col] = rook_piece
            rook_move = ((er, rook_start_col), (er, rook_end_col))

        return {
            "captured": captured,
            "en_passant_capture": en_passant_capture,
            "previous_castling_rights": previous_castling_rights,
            "previous_en_passant_target": previous_en_passant_target,
            "promoted_from": promoted_from,
            "rook_move": rook_move,
        }

    def undo_move(self, start, end, move_state):
        sr, sc = start
        er, ec = end

        piece = self.board[er][ec]
        captured = move_state["captured"]
        en_passant_capture = move_state["en_passant_capture"]
        promoted_from = move_state["promoted_from"]
        rook_move = move_state["rook_move"]

        if promoted_from is not None:
            piece = promoted_from

        if rook_move is not None:
            rook_start, rook_end = rook_move
            rsr, rsc = rook_start
            rer, rec = rook_end
            rook_piece = self.board[rer][rec]
            self.board[rer][rec] = "."
            self.board[rsr][rsc] = rook_piece

        self.board[sr][sc] = piece
        self.board[er][ec] = captured
        if en_passant_capture is not None:
            (capture_row, capture_col), captured_piece = en_passant_capture
            self.board[er][ec] = "."
            self.board[capture_row][capture_col] = captured_piece
        self.castling_rights = move_state["previous_castling_rights"]
        self.en_passant_target = move_state["previous_en_passant_target"]
