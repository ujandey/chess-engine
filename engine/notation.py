_FILES = "abcdefgh"
_RANKS = "87654321"


def square_name(row, col):
    return _FILES[col] + _RANKS[row]


def move_to_san(board, mg, start, end, promotion_choice=None):
    """Return Standard Algebraic Notation for the move start→end on board.

    The board must be in the state BEFORE the move. The function simulates the
    move internally (make_move / undo_move) only to detect check / checkmate.
    """
    sr, sc = start
    er, ec = end
    piece = board.get_piece(sr, sc)
    piece_type = piece.lower()

    def check_suffix():
        move_state = board.push(start, end, promotion_choice)
        opponent_is_white = not piece.isupper()
        try:
            if mg.is_checkmate(opponent_is_white):
                return "#"
            if mg.is_in_check(opponent_is_white):
                return "+"
            return ""
        finally:
            board.pop(move_state)

    # Castling
    if piece_type == "k" and abs(ec - sc) == 2:
        san = "O-O" if ec > sc else "O-O-O"
        return san + check_suffix()

    captured = board.get_piece(er, ec)
    is_ep = (
        piece_type == "p"
        and ec != sc
        and captured == "."
        and board.en_passant_target == (er, ec)
    )

    san = ""

    # Piece letter (none for pawns)
    if piece_type != "p":
        san += piece_type.upper()

    # Disambiguation: other same-type, same-colour pieces that can reach end
    if piece_type not in ("p", "k"):
        ambiguous = [
            (r, c)
            for r in range(8)
            for c in range(8)
            if (r, c) != start
            and board.get_piece(r, c).lower() == piece_type
            and board.get_piece(r, c).isupper() == piece.isupper()
            and end in mg.get_legal_moves(r, c)
        ]
        if ambiguous:
            same_file = any(c == sc for _, c in ambiguous)
            same_rank = any(r == sr for r, _ in ambiguous)
            if not same_file:
                san += _FILES[sc]
            elif not same_rank:
                san += _RANKS[sr]
            else:
                san += _FILES[sc] + _RANKS[sr]

    # Capture marker
    if captured != "." or is_ep:
        if piece_type == "p":
            san += _FILES[sc]
        san += "x"

    # Destination square
    san += square_name(er, ec)

    # Promotion
    if promotion_choice:
        san += "=" + promotion_choice.upper()
    elif piece_type == "p" and er in (0, 7):
        san += "=Q"

    # Check / checkmate suffix — simulate then undo
    san += check_suffix()

    return san
