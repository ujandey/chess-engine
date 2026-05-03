import datetime
import math
import threading
import tkinter as tk

from engine.board import Board
from engine.move_generator import MoveGenerator
from engine.notation import move_to_san

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

SQUARE_SIZE   = 60
EVAL_BAR_W    = 20
HISTORY_W     = 220
SEARCH_DEPTH  = 5

_PANEL_BG     = "#1E1E1E"
_PANEL_FG     = "#EEEEEE"
_DIM_FG       = "#888888"


def _score_to_ratio(score):
    if score >= 900:
        return 1.0
    if score <= -900:
        return 0.0
    return 0.5 + 0.5 * math.tanh(score / 4.0)


def _board_from_snapshot(snapshot):
    board = Board()
    board.board = [row[:] for row in snapshot["board"]]
    board.turn = snapshot["turn"]
    board.en_passant_target = snapshot["en_passant_target"]
    board.halfmove_clock = snapshot["halfmove_clock"]
    board.castling_rights = snapshot["castling_rights"].copy()
    board.position_counts = snapshot["position_counts"].copy()
    board.refresh_zobrist_hash()
    return board


# ---------------------------------------------------------------------------
# Game-tree node
# ---------------------------------------------------------------------------

class GameNode:
    _counter = 0

    def __init__(self, position, move=None, move_san="", parent=None):
        GameNode._counter += 1
        self.id = GameNode._counter
        self.position = position   # board snapshot dict
        self.move = move           # (start, end, promo_choice) or None
        self.move_san = move_san   # e.g. "e4", "O-O", "Nf3+"
        self.parent = parent
        self.children = []         # children[0] = main line


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

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

        # Game tree
        self._node_by_id = {}
        self.root_node = GameNode(self._capture())
        self.current_node = self.root_node

        self.best_move = None
        self._search_generation = 0

        board_size = 8 * SQUARE_SIZE
        self._build_layout(board_size)

        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Left>",  self.go_to_previous_position)
        self.root.bind("<Right>", self.go_to_next_position)

        self.draw_board()
        self.draw_eval_bar(0)
        self.update_history_panel()
        self._start_engine_search()

    # --- layout construction ----------------------------------------------

    def _build_layout(self, board_size):
        content = tk.Frame(self.root)
        content.pack()

        # Board
        self.canvas = tk.Canvas(content, width=board_size, height=board_size)
        self.canvas.pack(side="left")

        # Eval bar
        eval_frame = tk.Frame(content, padx=4)
        eval_frame.pack(side="left", fill="y")

        self.eval_canvas = tk.Canvas(
            eval_frame, width=EVAL_BAR_W, height=board_size, bg="#888888"
        )
        self.eval_canvas.pack()

        self.score_var = tk.StringVar(value="0.0")
        tk.Label(
            eval_frame,
            textvariable=self.score_var,
            font=("Arial", 9, "bold"),
            anchor="center",
        ).pack(fill="x")

        # History panel
        hist_frame = tk.Frame(content, bg=_PANEL_BG, padx=6, pady=6,
                               width=HISTORY_W)
        hist_frame.pack(side="left", fill="y")
        hist_frame.pack_propagate(False)

        tk.Label(hist_frame, text="MOVES", bg=_PANEL_BG, fg=_DIM_FG,
                 font=("Arial", 8, "bold"), anchor="w").pack(fill="x",
                                                              pady=(0, 4))

        text_frame = tk.Frame(hist_frame, bg=_PANEL_BG)
        text_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame, bg=_PANEL_BG,
                                  troughcolor="#333333", width=10)
        scrollbar.pack(side="right", fill="y")

        self.history_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            state="disabled",
            bg=_PANEL_BG,
            fg=_PANEL_FG,
            insertbackground=_PANEL_FG,
            selectbackground="#3A3A3A",
            relief="flat",
            padx=4, pady=4,
            cursor="",
            yscrollcommand=scrollbar.set,
        )
        self.history_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_text.yview)

        self.history_text.tag_config("mn",   foreground=_DIM_FG)
        self.history_text.tag_config("wm",   foreground=_PANEL_FG)
        self.history_text.tag_config("bm",   foreground="#CCCCCC")
        self.history_text.tag_config("cur",  background="#E8C45A",
                                      foreground=_PANEL_BG)
        self.history_text.tag_config("var",  foreground="#999999",
                                      font=("Arial", 9))
        self.history_text.tag_config("vb",   foreground="#666666")

        self.history_text.bind("<Button-1>", self._on_history_click)
        self.history_text.bind("<Motion>",   self._on_history_motion)

        self._pgn_btn = tk.Button(
            hist_frame, text="Copy PGN", command=self.export_pgn,
            font=("Arial", 9), bg="#2A2A2A", fg="#CCCCCC",
            activebackground="#3A3A3A", relief="flat", padx=4, pady=3,
        )
        self._pgn_btn.pack(fill="x", pady=(6, 0))

        # Status bar
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var,
            font=("Arial", 12), anchor="w", padx=8, pady=6,
        )
        self.status_label.pack(fill="x")

    # --- board snapshots --------------------------------------------------

    def _capture(self):
        return {
            "board": [row[:] for row in self.board.board],
            "turn": self.board.turn,
            "en_passant_target": self.board.en_passant_target,
            "halfmove_clock": self.board.halfmove_clock,
            "castling_rights": self.board.castling_rights.copy(),
            "position_counts": self.board.position_counts.copy(),
        }

    def _restore(self, position):
        self.board.board = [row[:] for row in position["board"]]
        self.board.turn = position["turn"]
        self.board.en_passant_target = position["en_passant_target"]
        self.board.halfmove_clock = position["halfmove_clock"]
        self.board.castling_rights = position["castling_rights"].copy()
        self.board.position_counts = position["position_counts"].copy()
        self.board.refresh_zobrist_hash()

    # --- game-tree navigation ---------------------------------------------

    def navigate_to_node(self, node):
        self.current_node = node
        self._restore(node.position)
        self.clear_selection()
        self.best_move = None
        self.update_history_panel()
        self.draw_board()
        self._start_engine_search()

    def record_move(self, start, end, san, promotion_choice):
        """Add a move to the tree. If it already exists as a child, just move
        the cursor there (no duplicate nodes)."""
        move_key = (start, end, promotion_choice)
        for child in self.current_node.children:
            if child.move == move_key:
                self.current_node = child
                self.update_history_panel()
                return
        node = GameNode(
            self._capture(),
            move=move_key,
            move_san=san,
            parent=self.current_node,
        )
        self._node_by_id[node.id] = node
        self.current_node.children.append(node)
        self.current_node = node
        self.update_history_panel()

    def go_to_previous_position(self, event=None):
        if self.current_node.parent is None:
            return
        self.navigate_to_node(self.current_node.parent)

    def go_to_next_position(self, event=None):
        if not self.current_node.children:
            return
        self.navigate_to_node(self.current_node.children[0])

    # --- history panel ----------------------------------------------------

    def update_history_panel(self):
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", "end")
        self._render_subtree(self.root_node, 1, True, after_var=False)
        self.history_text.config(state="disabled")
        # Scroll to the current move
        tag = f"nd{self.current_node.id}"
        ranges = self.history_text.tag_ranges(tag)
        if ranges:
            self.history_text.see(ranges[0])

    def _render_subtree(self, node, move_num, is_white, after_var):
        """Recursively write the game tree into self.history_text."""
        if not node.children:
            return

        main = node.children[0]

        # Move-number prefix
        if is_white or after_var:
            self.history_text.insert(
                "end",
                f"{move_num}. " if is_white else f"{move_num}… ",
                "mn",
            )

        # Main move text (clickable, highlighted if current)
        is_cur = main is self.current_node
        ntag = f"nd{main.id}"
        style = "cur" if is_cur else ("wm" if is_white else "bm")
        self.history_text.insert("end", main.move_san + " ", (ntag, style))

        # Inline variations
        had_var = False
        for var in node.children[1:]:
            had_var = True
            self.history_text.insert("end", "(", "vb")
            self.history_text.insert(
                "end",
                f"{move_num}. " if is_white else f"{move_num}… ",
                "mn",
            )
            is_cur_v = var is self.current_node
            vtag = f"nd{var.id}"
            vstyle = "cur" if is_cur_v else "var"
            self.history_text.insert("end", var.move_san + " ", (vtag, vstyle))
            next_vn = move_num + (0 if is_white else 1)
            self._render_subtree(var, next_vn, not is_white, after_var=False)
            self.history_text.insert("end", ") ", "vb")

        # Continue down the main line
        next_mn = move_num + (0 if is_white else 1)
        self._render_subtree(
            main, next_mn, not is_white,
            after_var=had_var and is_white,
        )

    def _on_history_click(self, event):
        idx = self.history_text.index(f"@{event.x},{event.y}")
        for tag in self.history_text.tag_names(idx):
            if tag.startswith("nd"):
                node = self._node_by_id.get(int(tag[2:]))
                if node:
                    self.navigate_to_node(node)
                return

    def _on_history_motion(self, event):
        idx = self.history_text.index(f"@{event.x},{event.y}")
        is_move = any(t.startswith("nd") for t in self.history_text.tag_names(idx))
        self.history_text.config(cursor="hand2" if is_move else "")

    # --- PGN export -------------------------------------------------------

    def export_pgn(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self._build_pgn())
        self._pgn_btn.config(text="Copied!")
        self.root.after(2000, lambda: self._pgn_btn.config(text="Copy PGN"))

    def _build_pgn(self):
        date_str = datetime.date.today().strftime("%Y.%m.%d")
        headers = "\n".join([
            '[Event "?"]', '[Site "?"]', f'[Date "{date_str}"]',
            '[White "?"]', '[Black "?"]', '[Result "*"]',
        ])
        tokens = self._pgn_tokens(self.root_node, 1, True, after_var=False)
        tokens.append("*")
        return headers + "\n\n" + " ".join(tokens)

    def _pgn_tokens(self, node, move_num, is_white, after_var):
        if not node.children:
            return []
        tokens = []
        main = node.children[0]
        if is_white or after_var:
            tokens.append(f"{move_num}." if is_white else f"{move_num}...")
        tokens.append(main.move_san)
        had_var = False
        for var in node.children[1:]:
            had_var = True
            tokens.append("(")
            tokens.append(f"{move_num}." if is_white else f"{move_num}...")
            tokens.append(var.move_san)
            next_vn = move_num + (0 if is_white else 1)
            tokens.extend(self._pgn_tokens(var, next_vn, not is_white, False))
            tokens.append(")")
        next_mn = move_num + (0 if is_white else 1)
        tokens.extend(
            self._pgn_tokens(main, next_mn, not is_white,
                              after_var=had_var and is_white)
        )
        return tokens

    # --- selection helpers ------------------------------------------------

    def clear_selection(self):
        self.selected = None
        self.legal_moves = []
        self.alert_king_square = None

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
                king_sq = self.mg.find_king(is_white)
                if king_sq:
                    highlights.add(king_sq)
        if self.alert_king_square:
            highlights.add(self.alert_king_square)
        return highlights

    def needs_promotion(self, start, end):
        piece = self.board.get_piece(start[0], start[1])
        return (piece == "P" and end[0] == 0) or (piece == "p" and end[0] == 7)

    def ask_promotion_choice(self, piece):
        color = "White" if piece.isupper() else "Black"
        chosen = {"value": None}
        dialog = tk.Toplevel(self.root)
        dialog.title("Pawn Promotion")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        tk.Label(dialog, text=f"{color} pawn promotion",
                 font=("Arial", 12, "bold"), padx=16, pady=10).pack()
        row_frame = tk.Frame(dialog, padx=12, pady=8)
        row_frame.pack()
        def choose(c):
            chosen["value"] = c
            dialog.destroy()
        for c in ["Q", "R", "B", "N"]:
            pkey = c if piece.isupper() else c.lower()
            tk.Button(row_frame, text=PIECES[pkey], font=("Arial", 28),
                      width=2, command=lambda v=c: choose(v)).pack(
                side="left", padx=6)
        tk.Button(dialog, text="Cancel", command=dialog.destroy,
                  padx=10, pady=4).pack(pady=(0, 12))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()
        return chosen["value"]

    # --- drawing ----------------------------------------------------------

    def draw_board(self):
        self.canvas.delete("all")
        check_highlights = self.get_check_highlights()
        game_status = self.mg.get_game_status()
        self.status_var.set(game_status["message"])

        for row in range(8):
            for col in range(8):
                x1, y1 = col * SQUARE_SIZE, row * SQUARE_SIZE
                x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=self.square_color(row, col), outline="")

                if self.selected == (row, col):
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill=SELECTED_SQUARE,
                        stipple="gray50", outline="")

                if (row, col) in check_highlights:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill=CHECK_SQUARE,
                        stipple="gray50", outline="")

                if (row, col) in self.legal_moves:
                    self.canvas.create_rectangle(
                        x1 + 4, y1 + 4, x2 - 4, y2 - 4,
                        outline=MOVE_OUTLINE, width=3)

                piece = self.board.get_piece(row, col)
                if PIECES[piece]:
                    self.canvas.create_text(
                        x1 + SQUARE_SIZE // 2, y1 + SQUARE_SIZE // 2,
                        text=PIECES[piece], font=("Arial", 32))

        if self.best_move and not game_status["is_over"]:
            self._draw_arrow(self.best_move[0], self.best_move[1])

    def _draw_arrow(self, start, end):
        sr, sc = start
        er, ec = end
        half = SQUARE_SIZE // 2
        self.canvas.create_rectangle(
            sc * SQUARE_SIZE, sr * SQUARE_SIZE,
            (sc + 1) * SQUARE_SIZE, (sr + 1) * SQUARE_SIZE,
            fill=BEST_FROM_COLOR, stipple="gray25", outline="")
        self.canvas.create_line(
            sc * SQUARE_SIZE + half, sr * SQUARE_SIZE + half,
            ec * SQUARE_SIZE + half, er * SQUARE_SIZE + half,
            fill=ARROW_COLOR, width=5,
            arrow=tk.LAST, arrowshape=(14, 18, 6), capstyle=tk.ROUND)

    def draw_eval_bar(self, score):
        h = 8 * SQUARE_SIZE
        self.eval_canvas.delete("all")
        black_h = int(h * (1.0 - _score_to_ratio(score)))
        self.eval_canvas.create_rectangle(
            0, 0, EVAL_BAR_W, black_h, fill=EVAL_BLACK, outline="")
        self.eval_canvas.create_rectangle(
            0, black_h, EVAL_BAR_W, h, fill=EVAL_WHITE, outline="")
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

    # --- engine search ----------------------------------------------------

    def _start_engine_search(self):
        self._search_generation += 1
        generation = self._search_generation
        game_status = self.mg.get_game_status()
        if game_status["is_over"]:
            self.best_move = None
            self.draw_eval_bar(self.mg.evaluate_position())
            self.draw_board()
            return

        self.score_var.set("...")
        snapshot = self._capture()
        is_white = self.board.turn == "white"
        threading.Thread(
            target=self._engine_thread,
            args=(snapshot, is_white, generation),
            daemon=True,
        ).start()

    def _engine_thread(self, snapshot, is_white, generation):
        mg = MoveGenerator(_board_from_snapshot(snapshot))
        best_move, score = mg.find_best_move(SEARCH_DEPTH, is_white)
        self.root.after(0, lambda: self._on_engine_done(best_move, score, generation))

    def _on_engine_done(self, best_move, score, generation):
        if generation != self._search_generation:
            return
        self.best_move = best_move
        self.draw_eval_bar(score)
        self.draw_board()

    # --- click handler ----------------------------------------------------

    def select_piece(self, row, col):
        self.selected = (row, col)
        self.legal_moves = self.mg.get_legal_moves(row, col)
        self.alert_king_square = None

    def on_click(self, event):
        # No is_latest_position guard — moves from any node create a new branch
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

            # Compute SAN before the move mutates the board
            san = move_to_san(self.board, self.mg, start, end, promotion_choice)
            self.board.move_piece(start, end, promotion_choice)
            self.clear_selection()
            self.record_move(start, end, san, promotion_choice)
            self.best_move = None
            self.draw_board()
            self._start_engine_search()
            return

        if self.is_current_turn_piece(piece):
            self.select_piece(row, col)
        else:
            self.alert_king_square = (
                self.mg.find_king(start_piece.isupper())
                if end in pseudo_moves else None
            )

        self.draw_board()

    def run(self):
        self.root.mainloop()
