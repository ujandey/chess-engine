import tkinter as tk

from engine.board import Board
from engine.move_generator import MoveGenerator

PIECES = {
    "K": "\u2654",
    "Q": "\u2655",
    "R": "\u2656",
    "B": "\u2657",
    "N": "\u2658",
    "P": "\u2659",
    "k": "\u265A",
    "q": "\u265B",
    "r": "\u265C",
    "b": "\u265D",
    "n": "\u265E",
    "p": "\u265F",
    ".": "",
}

LIGHT_SQUARE = "#EEEED2"
DARK_SQUARE = "#769656"
SELECTED_SQUARE = "#F6F669"
CHECK_SQUARE = "#D9534F"
MOVE_OUTLINE = "#1F6FEB"
SQUARE_SIZE = 60


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

        board_size = 8 * SQUARE_SIZE
        self.canvas = tk.Canvas(self.root, width=board_size, height=board_size)
        self.canvas.pack()
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Arial", 12),
            anchor="w",
            padx=8,
            pady=6,
        )
        self.status_label.pack(fill="x")

        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Left>", self.go_to_previous_position)
        self.root.bind("<Right>", self.go_to_next_position)

        self.draw_board()

    def capture_position(self):
        return {
            "board": [row[:] for row in self.board.board],
            "turn": self.board.turn,
            "en_passant_target": self.board.en_passant_target,
            "halfmove_clock": self.board.halfmove_clock,
            "castling_rights": self.board.castling_rights.copy(),
        }

    def restore_position(self, position):
        self.board.board = [row[:] for row in position["board"]]
        self.board.turn = position["turn"]
        self.board.en_passant_target = position["en_passant_target"]
        self.board.halfmove_clock = position["halfmove_clock"]
        self.board.castling_rights = position["castling_rights"].copy()

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
        self.draw_board()

    def go_to_next_position(self, event=None):
        if self.history_index >= len(self.history) - 1:
            return

        self.history_index += 1
        self.restore_position(self.history[self.history_index])
        self.clear_selection()
        self.draw_board()

    def is_current_turn_piece(self, piece):
        if piece == ".":
            return False

        if self.board.turn == "white":
            return piece.isupper()
        return piece.islower()

    def square_color(self, row, col):
        if (row + col) % 2 == 0:
            return LIGHT_SQUARE
        return DARK_SQUARE

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
            dialog,
            text="Cancel",
            command=dialog.destroy,
            padx=10,
            pady=4,
        ).pack(pady=(0, 12))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()

        return selected_choice["value"]

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
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=self.square_color(row, col),
                    outline="",
                )

                if self.selected == (row, col):
                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=SELECTED_SQUARE,
                        stipple="gray50",
                        outline="",
                    )

                if (row, col) in check_highlights:
                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=CHECK_SQUARE,
                        stipple="gray50",
                        outline="",
                    )

                if (row, col) in self.legal_moves:
                    self.canvas.create_rectangle(
                        x1 + 4,
                        y1 + 4,
                        x2 - 4,
                        y2 - 4,
                        outline=MOVE_OUTLINE,
                        width=3,
                    )

                piece = self.board.get_piece(row, col)
                if PIECES[piece]:
                    self.canvas.create_text(
                        x1 + SQUARE_SIZE // 2,
                        y1 + SQUARE_SIZE // 2,
                        text=PIECES[piece],
                        font=("Arial", 32),
                    )

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
