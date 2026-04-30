import math
import threading
import tkinter as tk

from engine.board import Board
from engine.move_generator import MoveGenerator

PIECES = {
    "K": "♔", "Q": "♕", "R": "♖",
    "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜",
    "b": "♝", "n": "♞", "p": "♟",
    ".": "",
}

LIGHT_SQUARE    = "#EEEED2"
DARK_SQUARE     = "#769656"
SELECTED_SQUARE = "#F6F669"
CHECK_SQUARE    = "#D9534F"
MOVE_OUTLINE    = "#1F6FEB"
BEST_FROM_COLOR = "#FF9F00"
ARROW_COLOR     = "#D97000"
EVAL_WHITE      = "#F0F0F0"
EVAL_BLACK      = "#1A1A1A"

SQUARE_SIZE  = 60
EVAL_BAR_W   = 20
SEARCH_DEPTH = 3


def _score_to_ratio(score):
    """Map engine score to [0, 1]: 1.0 = full white advantage, 0.0 = full black."""
    if score >= 900:
        return 1.0
    if score <= -900:
        return 0.0
    return 0.5 + 0.5 * math.tanh(score / 4.0)


class ChessGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Suar Chess Engine")

        self.board = Board()
        self.mg = MoveGenerator(self.board)

        self.selected = None
        self.legal_moves = []
        self.alert_king_square = None
        self.status_var = tk.StringVar()

        self.history = [self.capture_position()]
        self.history_index = 0

        self.best_move = None
        self._search_generation = 0

        board_size = 8 * SQUARE_SIZE

        # ----- layout -----------------------------------------------------
        content = tk.Frame(self.root)
        content.pack()

        self.canvas = tk.Canvas(content, width=board_size, height=board_size)
        self.canvas.pack(side="left")

        sidebar = tk.Frame(content, padx=4)
        sidebar.pack(side="left", fill="y")

        self.eval_canvas = tk.Canvas(
            sidebar, width=EVAL_BAR_W, height=board_size, bg="#888888"
        )
        self.eval_canvas.pack()

        self.score_var = tk.StringVar(value="0.0")
        tk.Label(
            sidebar,
            textvariable=self.score_var,
            font=("Arial", 9, "bold"),
            anchor="center",
        ).pack(fill="x")

        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Arial", 12),
            anchor="w",
            padx=8,
            pady=6,
        )
        self.status_label.pack(fill="x")
        # ------------------------------------------------------------------

        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Left>", self.go_to_previous_position)
        self.root.bind("<Right>", self.go_to_next_position)

        self.draw_board()
        self.draw_eval_bar(0)
        self._start_engine_search()

    # --- snapshots --------------------------------------------------------

    def capture_position(self):
        return {
            "board": [row[:] for row in self.board.board],
            "turn": self.board.turn,
            "en_passant_target": self.board.en_passant_target,
            "halfmove_clock": self.board.halfmove_clock,
            "castling_rights": self.board.castling_rights.copy(),
            "position_counts": self.board.position_counts.copy(),
        }

    def restore_position(self, position):
        self.board.board = [row[:] for row in position["board"]]
        self.board.turn = position["turn"]
        self.board.en_passant_target = position["en_passant_target"]
        self.board.halfmove_clock = position["halfmove_clock"]
        self.board.castling_rights = position["castling_rights"].copy()
        self.board.position_counts = position["position_counts"].copy()

    # --- selection --------------------------------------------------------

    def clear_selection(self):
        self.selected = None
        self.legal_moves = []
        self.alert_king_square = None

    def record_position(self):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]
        self.history.append(self.capture_position())
        self.history_index = len(self.history) - 1

    def is_latest_position(self):
        return self.history_index == len(self.history) - 1

    def go_to_previous_position(self, event=None):
        if self.history_index == 0:
            return
        self.history_index -= 1
        self.restore_position(self.history[self.history_index])
        self.clear_selection()
        self.best_move = None
        self.draw_board()
        self._start_engine_search()

    def go_to_next_position(self, event=None):
        if self.history_index >= len(self.history) - 1:
            return
        self.history_index += 1
        self.restore_position(self.history[self.history_index])
        self.clear_selection()
        self.best_move = None
        self.draw_board()
        self._start_engine_search()

    # --- helpers ----------------------------------------------------------

    def is_current_turn_piece(self, piece):
        if piece == ".":
            return False
        return piece.isupper() if self.board.turn == "white" else piece.islower()

    def square_color(self, row, col):
        return LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

    def get_check_highlights(self):
        highlights = set()
        for is_white in (True, False):
            if self.mg.is_in_check(is_white):
                king_square = self.mg.find_king(is_white)
                if king_square is not None:
                    highlights.add(king_square)
        if self.alert_king_square is not None:
            highlights.add(self.alert_king_square)
        return highlights

    def needs_promotion(self, start, end):
        piece = self.board.get_piece(start[0], start[1])
        return (piece == "P" and end[0] == 0) or (piece == "p" and end[0] == 7)

    def ask_promotion_choice(self, piece):
        color = "White" if piece.isupper() else "Black"
        choices = ["Q", "R", "B", "N"]
        selected_choice = {"value": None}

        dialog = tk.Toplevel(self.root)
        dialog.title("Pawn Promotion")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text=f"{color} pawn promotion",
            font=("Arial", 12, "bold"),
            padx=16,
            pady=10,
        ).pack()

        button_row = tk.Frame(dialog, padx=12, pady=8)
        button_row.pack()

        def choose(choice):
            selected_choice["value"] = choice
            dialog.destroy()

        for choice in choices:
            piece_key = choice if piece.isupper() else choice.lower()
            tk.Button(
                button_row,
                text=PIECES[piece_key],
                font=("Arial", 28),
                width=2,
                command=lambda value=choice: choose(value),
            ).pack(side="left", padx=6)

        tk.Button(
            dialog, text="Cancel", command=dialog.destroy, padx=10, pady=4
        ).pack(pady=(0, 12))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()
        return selected_choice["value"]

    # --- drawing ----------------------------------------------------------

    def draw_board(self):
        self.canvas.delete("all")
        check_highlights = self.get_check_highlights()
        game_status = self.mg.get_game_status()
        self.status_var.set(game_status["message"])

        for row in range(8):
            for col in range(8):
                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=self.square_color(row, col), outline=""
                )

                if self.selected == (row, col):
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=SELECTED_SQUARE, stipple="gray50", outline="",
                    )

                if (row, col) in check_highlights:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=CHECK_SQUARE, stipple="gray50", outline="",
                    )

                if (row, col) in self.legal_moves:
                    self.canvas.create_rectangle(
                        x1 + 4, y1 + 4, x2 - 4, y2 - 4,
                        outline=MOVE_OUTLINE, width=3,
                    )

                piece = self.board.get_piece(row, col)
                if PIECES[piece]:
                    self.canvas.create_text(
                        x1 + SQUARE_SIZE // 2,
                        y1 + SQUARE_SIZE // 2,
                        text=PIECES[piece],
                        font=("Arial", 32),
                    )

        if self.best_move is not None and not game_status["is_over"]:
            self._draw_best_move_arrow(self.best_move[0], self.best_move[1])

    def _draw_best_move_arrow(self, start, end):
        sr, sc = start
        er, ec = end
        half = SQUARE_SIZE // 2

        # translucent highlight on origin square
        self.canvas.create_rectangle(
            sc * SQUARE_SIZE, sr * SQUARE_SIZE,
            (sc + 1) * SQUARE_SIZE, (sr + 1) * SQUARE_SIZE,
            fill=BEST_FROM_COLOR, stipple="gray25", outline="",
        )
        # arrow from centre of start square to centre of end square
        self.canvas.create_line(
            sc * SQUARE_SIZE + half, sr * SQUARE_SIZE + half,
            ec * SQUARE_SIZE + half, er * SQUARE_SIZE + half,
            fill=ARROW_COLOR, width=5,
            arrow=tk.LAST, arrowshape=(14, 18, 6),
            capstyle=tk.ROUND,
        )

    def draw_eval_bar(self, score):
        h = 8 * SQUARE_SIZE
        self.eval_canvas.delete("all")
        ratio = _score_to_ratio(score)
        black_h = int(h * (1.0 - ratio))

        self.eval_canvas.create_rectangle(
            0, 0, EVAL_BAR_W, black_h, fill=EVAL_BLACK, outline=""
        )
        self.eval_canvas.create_rectangle(
            0, black_h, EVAL_BAR_W, h, fill=EVAL_WHITE, outline=""
        )

        if score >= 900:
            text = "+M"
        elif score <= -900:
            text = "-M"
        elif score > 0:
            text = f"+{score:.1f}"
        elif score < 0:
            text = f"{score:.1f}"
        else:
            text = "0.0"
        self.score_var.set(text)

    # --- engine search (background thread) --------------------------------

    def _start_engine_search(self):
        if self.mg.get_game_status()["is_over"]:
            self.best_move = None
            self.draw_board()
            return

        self._search_generation += 1
        generation = self._search_generation
        self.score_var.set("...")

        snapshot = self.capture_position()
        is_white = self.board.turn == "white"

        t = threading.Thread(
            target=self._engine_thread,
            args=(snapshot, is_white, generation),
            daemon=True,
        )
        t.start()

    def _engine_thread(self, snapshot, is_white, generation):
        b = Board()
        b.board = [row[:] for row in snapshot["board"]]
        b.turn = snapshot["turn"]
        b.en_passant_target = snapshot["en_passant_target"]
        b.halfmove_clock = snapshot["halfmove_clock"]
        b.castling_rights = snapshot["castling_rights"].copy()
        b.position_counts = snapshot["position_counts"].copy()

        mg = MoveGenerator(b)
        best_move, score = mg.find_best_move(SEARCH_DEPTH, is_white)

        self.root.after(0, lambda: self._on_engine_done(best_move, score, generation))

    def _on_engine_done(self, best_move, score, generation):
        if generation != self._search_generation:
            return  # result is from a superseded search — discard
        self.best_move = best_move
        self.draw_eval_bar(score)
        self.draw_board()

    # --- click handler ----------------------------------------------------

    def select_piece(self, row, col):
        self.selected = (row, col)
        self.legal_moves = self.mg.get_legal_moves(row, col)
        self.alert_king_square = None

    def on_click(self, event):
        if not self.is_latest_position():
            return
        if self.mg.get_game_status()["is_over"]:
            return

        row = event.y // SQUARE_SIZE
        col = event.x // SQUARE_SIZE
        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board.get_piece(row, col)

        if self.selected is None:
            if self.is_current_turn_piece(piece):
                self.select_piece(row, col)
            self.draw_board()
            return

        start = self.selected
        end = (row, col)
        start_piece = self.board.get_piece(start[0], start[1])
        legal_moves = self.legal_moves
        pseudo_moves = self.mg.get_piece_moves(start[0], start[1])

        if end in legal_moves:
            promotion_choice = None
            if self.needs_promotion(start, end):
                promotion_choice = self.ask_promotion_choice(start_piece)
                if promotion_choice is None:
                    self.draw_board()
                    return

            self.board.move_piece(start, end, promotion_choice)
            self.clear_selection()
            self.record_position()
            self.best_move = None
            self.draw_board()
            self._start_engine_search()
            return
        elif self.is_current_turn_piece(piece):
            self.select_piece(row, col)
        else:
            if end in pseudo_moves:
                self.alert_king_square = self.mg.find_king(start_piece.isupper())
            else:
                self.alert_king_square = None

        self.draw_board()

    def run(self):
        self.root.mainloop()
