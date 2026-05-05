import random


_ZOBRIST_RNG = random.Random(20260501)


class Board:
    PIECE_TO_ZOBRIST_INDEX = {
        "P": 0, "N": 1, "B": 2, "R": 3, "Q": 4, "K": 5,
        "p": 6, "n": 7, "b": 8, "r": 9, "q": 10, "k": 11,
    }
    ZOBRIST_PIECES = [
        [
            [_ZOBRIST_RNG.getrandbits(64) for _ in range(12)]
            for _ in range(8)
        ]
        for _ in range(8)
    ]
    ZOBRIST_SIDE_TO_MOVE = _ZOBRIST_RNG.getrandbits(64)
    ZOBRIST_CASTLING = [_ZOBRIST_RNG.getrandbits(64) for _ in range(16)]
    ZOBRIST_EN_PASSANT = [_ZOBRIST_RNG.getrandbits(64) for _ in range(8)]

    def __init__(self):
        self.board = self.create_starting_position()
        self.turn = "white"
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.castling_rights = {
            "white_kingside": True,
            "white_queenside": True,
            "black_kingside": True,
            "black_queenside": True,
        }
        # Cached king positions — updated incrementally in make_move/undo_move
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.piece_positions = self.compute_piece_positions()
        self._piece_hash = self.compute_piece_hash()
        self.position_counts = {self.get_position_key(): 1}

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

    def _xor_piece_hash(self, piece, row, col):
        if piece != ".":
            piece_index = self.PIECE_TO_ZOBRIST_INDEX[piece]
            self._piece_hash ^= self.ZOBRIST_PIECES[row][col][piece_index]

    def compute_piece_positions(self):
        positions = {"white": set(), "black": set()}
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == ".":
                    continue
                side = "white" if piece.isupper() else "black"
                positions[side].add((row, col))
        return positions

    def _remove_piece_position(self, piece, row, col):
        if piece == ".":
            return
        side = "white" if piece.isupper() else "black"
        self.piece_positions[side].discard((row, col))

    def _add_piece_position(self, piece, row, col):
        if piece == ".":
            return
        side = "white" if piece.isupper() else "black"
        self.piece_positions[side].add((row, col))

    def iter_side_pieces(self, is_white):
        side = "white" if is_white else "black"
        return tuple(self.piece_positions[side])

    def compute_piece_hash(self):
        piece_hash = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != ".":
                    piece_index = self.PIECE_TO_ZOBRIST_INDEX[piece]
                    piece_hash ^= self.ZOBRIST_PIECES[row][col][piece_index]
        return piece_hash

    def refresh_zobrist_hash(self):
        self._piece_hash = self.compute_piece_hash()
        self.piece_positions = self.compute_piece_positions()
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == "K":
                    self.white_king_pos = (row, col)
                elif piece == "k":
                    self.black_king_pos = (row, col)

    def get_castling_state_index(self):
        cr = self.castling_rights
        return (
            (1 if cr["white_kingside"] else 0)
            | (2 if cr["white_queenside"] else 0)
            | (4 if cr["black_kingside"] else 0)
            | (8 if cr["black_queenside"] else 0)
        )

    @property
    def zobrist_hash(self):
        value = self._piece_hash
        if self.turn == "black":
            value ^= self.ZOBRIST_SIDE_TO_MOVE
        value ^= self.ZOBRIST_CASTLING[self.get_castling_state_index()]
        if self.en_passant_target is not None:
            value ^= self.ZOBRIST_EN_PASSANT[self.en_passant_target[1]]
        return value

    def to_fen(self, halfmove_clock=None, fullmove_number=1):
        rows = []
        for row in self.board:
            empty_count = 0
            fen_row = []

            for piece in row:
                if piece == ".":
                    empty_count += 1
                else:
                    if empty_count:
                        fen_row.append(str(empty_count))
                        empty_count = 0
                    fen_row.append(piece)

            if empty_count:
                fen_row.append(str(empty_count))

            rows.append("".join(fen_row))

        active_color = "w" if self.turn == "white" else "b"

        castling = []
        if self.castling_rights["white_kingside"]:
            castling.append("K")
        if self.castling_rights["white_queenside"]:
            castling.append("Q")
        if self.castling_rights["black_kingside"]:
            castling.append("k")
        if self.castling_rights["black_queenside"]:
            castling.append("q")
        castling_field = "".join(castling) if castling else "-"

        if self.en_passant_target is None:
            en_passant = "-"
        else:
            ep_row, ep_col = self.en_passant_target
            en_passant = f"{chr(ord('a') + ep_col)}{8 - ep_row}"

        if halfmove_clock is None:
            halfmove_clock = self.halfmove_clock

        return (
            f"{'/'.join(rows)} {active_color} {castling_field} "
            f"{en_passant} {halfmove_clock} {fullmove_number}"
        )

    def set_fen(self, fen):
        fields = fen.strip().split()
        if len(fields) < 4:
            raise ValueError("FEN must include board, turn, castling, and en-passant fields")

        board_field, active_color, castling_field, ep_field = fields[:4]
        halfmove_clock = int(fields[4]) if len(fields) > 4 else 0

        rows = board_field.split("/")
        if len(rows) != 8:
            raise ValueError("FEN board must contain 8 ranks")

        board = []
        white_king = None
        black_king = None
        for row_index, fen_row in enumerate(rows):
            row = []
            for char in fen_row:
                if char.isdigit():
                    row.extend(["."] * int(char))
                elif char in self.PIECE_TO_ZOBRIST_INDEX:
                    if char == "K":
                        white_king = (row_index, len(row))
                    elif char == "k":
                        black_king = (row_index, len(row))
                    row.append(char)
                else:
                    raise ValueError(f"Invalid FEN piece: {char}")
            if len(row) != 8:
                raise ValueError("Each FEN rank must contain 8 squares")
            board.append(row)

        if white_king is None or black_king is None:
            raise ValueError("FEN must contain both kings")

        self.board = board
        self.turn = "white" if active_color == "w" else "black"
        self.castling_rights = {
            "white_kingside": "K" in castling_field,
            "white_queenside": "Q" in castling_field,
            "black_kingside": "k" in castling_field,
            "black_queenside": "q" in castling_field,
        }
        if ep_field == "-":
            self.en_passant_target = None
        else:
            self.en_passant_target = (8 - int(ep_field[1]), ord(ep_field[0]) - ord("a"))
        self.halfmove_clock = halfmove_clock
        self.white_king_pos = white_king
        self.black_king_pos = black_king
        self.refresh_zobrist_hash()
        self.position_counts = {self.get_position_key(): 1}

    def get_position_key(self):
        return self.zobrist_hash

    def record_current_position(self):
        position_key = self.get_position_key()
        self.position_counts[position_key] = self.position_counts.get(position_key, 0) + 1

    def get_promotion_piece(self, piece, promotion_choice=None):
        if promotion_choice is None:
            return "Q" if piece.isupper() else "q"

        normalized_choice = promotion_choice.upper()
        if normalized_choice not in {"Q", "R", "B", "N"}:
            normalized_choice = "Q"

        return normalized_choice if piece.isupper() else normalized_choice.lower()

    def _switch_turn(self):
        self.turn = "black" if self.turn == "white" else "white"

    def move_piece(self, start, end, promotion_choice=None):
        self.push(start, end, promotion_choice)

    def push(self, start, end, promotion_choice=None):
        previous_turn = self.turn
        move_state = self.make_move(start, end, promotion_choice)
        self._switch_turn()
        position_key = self.get_position_key()
        self.position_counts[position_key] = self.position_counts.get(position_key, 0) + 1
        move_state.update({
            "start": start,
            "end": end,
            "promotion_choice": promotion_choice,
            "previous_turn": previous_turn,
            "pushed_position_key": position_key,
        })
        return move_state

    def pop(self, move_state):
        position_key = move_state["pushed_position_key"]
        count = self.position_counts.get(position_key, 0)
        if count <= 1:
            self.position_counts.pop(position_key, None)
        else:
            self.position_counts[position_key] = count - 1

        self.turn = move_state["previous_turn"]
        self.undo_move(move_state["start"], move_state["end"], move_state)

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
        previous_halfmove_clock = self.halfmove_clock
        previous_piece_hash = self._piece_hash
        rook_move = None
        en_passant_capture = None
        promoted_from = None

        self._xor_piece_hash(piece, sr, sc)
        self._remove_piece_position(piece, sr, sc)
        if captured != ".":
            self._xor_piece_hash(captured, er, ec)
            self._remove_piece_position(captured, er, ec)

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
            self._xor_piece_hash(captured, capture_row, ec)
            self._remove_piece_position(captured, capture_row, ec)
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

        self._xor_piece_hash(self.board[er][ec], er, ec)
        self._add_piece_position(self.board[er][ec], er, ec)

        if piece.lower() == "p" or captured != ".":
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if piece.lower() == "p" and abs(er - sr) == 2:
            self.en_passant_target = ((sr + er) // 2, sc)

        is_castle = piece in ("K", "k") and abs(ec - sc) == 2
        if is_castle:
            rook_start_col = 7 if ec > sc else 0
            rook_end_col = 5 if ec > sc else 3
            rook_piece = self.board[er][rook_start_col]
            self._xor_piece_hash(rook_piece, er, rook_start_col)
            self._remove_piece_position(rook_piece, er, rook_start_col)
            self.board[er][rook_start_col] = "."
            self.board[er][rook_end_col] = rook_piece
            self._xor_piece_hash(rook_piece, er, rook_end_col)
            self._add_piece_position(rook_piece, er, rook_end_col)
            rook_move = ((er, rook_start_col), (er, rook_end_col))

        # Incrementally update cached king positions (O(1) vs O(64) scan)
        prev_white_king_pos = self.white_king_pos
        prev_black_king_pos = self.black_king_pos
        if piece == "K":
            self.white_king_pos = (er, ec)
        elif piece == "k":
            self.black_king_pos = (er, ec)

        return {
            "captured": captured,
            "en_passant_capture": en_passant_capture,
            "previous_castling_rights": previous_castling_rights,
            "previous_en_passant_target": previous_en_passant_target,
            "previous_halfmove_clock": previous_halfmove_clock,
            "previous_piece_hash": previous_piece_hash,
            "promoted_from": promoted_from,
            "rook_move": rook_move,
            "prev_white_king_pos": prev_white_king_pos,
            "prev_black_king_pos": prev_black_king_pos,
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
            self._remove_piece_position(rook_piece, rer, rec)
            self.board[rer][rec] = "."
            self.board[rsr][rsc] = rook_piece
            self._add_piece_position(rook_piece, rsr, rsc)

        self._remove_piece_position(self.board[er][ec], er, ec)
        self.board[sr][sc] = piece
        self.board[er][ec] = captured
        self._add_piece_position(piece, sr, sc)
        self._add_piece_position(captured, er, ec)
        if en_passant_capture is not None:
            (capture_row, capture_col), captured_piece = en_passant_capture
            self._remove_piece_position(captured, er, ec)
            self.board[er][ec] = "."
            self.board[capture_row][capture_col] = captured_piece
            self._add_piece_position(captured_piece, capture_row, capture_col)
        self.castling_rights = move_state["previous_castling_rights"]
        self.en_passant_target = move_state["previous_en_passant_target"]
        self.halfmove_clock = move_state["previous_halfmove_clock"]
        self._piece_hash = move_state["previous_piece_hash"]
        self.white_king_pos = move_state["prev_white_king_pos"]
        self.black_king_pos = move_state["prev_black_king_pos"]
