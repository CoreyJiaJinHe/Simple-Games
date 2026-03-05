# Snakes and Ladders game logic + GUI.
import random
import sys
from math import ceil

from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Node:
    def __init__(self, position):
        self.position = position
        self.next = None
        self.snake = None
        self.ladder = None


class BoardOverlay(QWidget):
    """Draw snake/ladder connector lines over the board cells."""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.owner.game is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Ladders: green lines from base -> top.
        painter.setPen(QPen(QColor("#198754"), 3))
        for start, end in self.owner._ladder_bases.items():
            p1, p2 = self.owner._segment_between_cells(start, end)
            if p1 is None or p2 is None:
                continue
            painter.drawLine(p1, p2)

        # Snakes: red lines from head -> tail.
        painter.setPen(QPen(QColor("#dc3545"), 3))
        for start, end in self.owner._snake_heads.items():
            p1, p2 = self.owner._segment_between_cells(start, end)
            if p1 is None or p2 is None:
                continue
            painter.drawLine(p1, p2)


class Snakes_And_Ladder:
    def __init__(self, board_size: int, snakes: int, ladders: int):
        self.board_size = board_size
        self.generate_board(snakes, ladders)
        self.player_position = 0
        self.bot_position = 0

    def generate_board(self, snakes: int, ladders: int):
        # Generate the board as a linked list of positions 0..board_size-1.
        self.head = Node(0)
        current = self.head
        for i in range(1, self.board_size):
            new_node = Node(i)
            current.next = new_node
            current = new_node

        # Generate snakes from unique head nodes.
        snake_head_candidates = list(range(1, self.board_size - 2))
        snake_heads = random.sample(snake_head_candidates, k=min(snakes, len(snake_head_candidates)))

        for head in snake_heads:
            tail = random.randrange(0, head)
            head_node = self.grab_node(head)
            tail_node = self.grab_node(tail)
            if head_node and tail_node:
                head_node.snake = tail_node

        # Generate ladders from unique bottom nodes that are NOT snake heads.
        ladder_bottom_candidates = [
            position for position in range(0, self.board_size - 2)
            if position not in snake_heads
        ]
        ladder_bottoms = random.sample(ladder_bottom_candidates, k=min(ladders, len(ladder_bottom_candidates)))

        for bottom in ladder_bottoms:
            top = random.randrange(bottom + 1, self.board_size)
            bottom_node = self.grab_node(bottom)
            top_node = self.grab_node(top)
            if bottom_node and top_node:
                bottom_node.ladder = top_node

    def grab_node(self, position):
        current = self.head
        while current is not None:
            if current.position == position:
                return current
            current = current.next
        return None

    def dice_roll(self):
        return random.randint(1, 6)

    def move(self, position, dice_roll: int):
        new_position = position + dice_roll
        if new_position > self.board_size - 1:
            return position

        new_node = self.grab_node(new_position)
        if new_node.snake:
            return new_node.snake.position
        if new_node.ladder:
            return new_node.ladder.position
        return new_position

    def check_winner(self):
        if self.player_position >= self.board_size - 1:
            return "Player"
        if self.bot_position >= self.board_size - 1:
            return "Bot"
        return None

    # -------- CLI helpers --------
    def play_turn(self, player: str):
        dice_roll = self.dice_roll()
        print(f"{player} rolled a {dice_roll}")
        if player == "Player":
            self.player_position = self.move(self.player_position, dice_roll)
            print(f"Player is now at position {self.player_position}")
        else:
            self.bot_position = self.move(self.bot_position, dice_roll)
            print(f"Bot is now at position {self.bot_position}")

    def play_game(self):
        count = 1
        while True:
            print("Turn:", count)
            self.play_turn("Player")
            winner = self.check_winner()
            if winner:
                print(f"{winner} wins!")
                break

            self.play_turn("Bot")
            winner = self.check_winner()
            if winner:
                print(f"{winner} wins!")
                break

            count += 1
            if count == 200:
                print("Game is a draw!")
                break

    def debug_print_board(self):
        current = self.head
        while current is not None:
            print(
                f"Position: {current.position}, "
                f"Snake: {current.snake.position if current.snake else None}, "
                f"Ladder: {current.ladder.position if current.ladder else None}"
            )
            current = current.next

    def debug_print_board_v2(self):
        board = ["." for _ in range(self.board_size)]
        current = self.head
        while current is not None:
            if current.snake:
                board[current.position] = "S"
            elif current.ladder:
                board[current.position] = "L"
            current = current.next
        for i in range(0, self.board_size, 10):
            print(" ".join(board[i : i + 10]))


class SnLGUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Snakes and Ladders")
        self.setMinimumSize(850, 700)

        self.game = None
        self._snake_heads = {}
        self._ladder_bases = {}
        self._board_labels = {}
        self._columns = 10
        self._rows = 0
        self._auto_running = False
        self._next_actor = "Player"
        self._turn_delay_ms = 750

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout()

        controls = QHBoxLayout()
        self.start_button = QPushButton("Start Game")
        self.start_button.clicked.connect(self.on_start_clicked)

        self.roll_button = QPushButton("Roll Dice")
        self.roll_button.setEnabled(False)
        self.roll_button.clicked.connect(self.on_roll_clicked)

        controls.addWidget(self.start_button)
        controls.addWidget(self.roll_button)
        controls.addStretch()

        self.status_label = QLabel("Click Start Game to configure board size, snakes, and ladders.")
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setWordWrap(True)

        self.board_scroll = QScrollArea()
        self.board_scroll.setWidgetResizable(True)

        self.board_widget = QWidget()
        self.board_grid = QGridLayout()
        self.board_grid.setSpacing(5)
        self.board_widget.setLayout(self.board_grid)
        self.board_overlay = BoardOverlay(self, self.board_widget)
        self.board_scroll.setWidget(self.board_widget)

        root.addLayout(controls)
        root.addWidget(self.status_label)
        root.addWidget(self.board_scroll)
        self.setLayout(root)

    def _ask_game_settings(self):
        board_size, ok = QInputDialog.getInt(self, "Board Size", "Board size:", 100, 20, 400)
        if not ok:
            return None

        snake_max = max(0, board_size - 2)
        snakes, ok = QInputDialog.getInt(self, "Snakes", "Number of snakes:", 10, 0, snake_max)
        if not ok:
            return None

        ladder_max = max(0, board_size - 2)
        ladders, ok = QInputDialog.getInt(self, "Ladders", "Number of ladders:", 10, 0, ladder_max)
        if not ok:
            return None

        return board_size, snakes, ladders

    def on_start_clicked(self):
        if self._auto_running:
            return

        settings = self._ask_game_settings()
        if settings is None:
            return

        board_size, snakes, ladders = settings
        self.game = Snakes_And_Ladder(board_size=board_size, snakes=snakes, ladders=ladders)
        self._extract_special_positions()
        self._build_board_cells()
        self._render_board()

        self._next_actor = "Player"
        self.roll_button.setEnabled(True)
        self.start_button.setText("New Game")
        self.status_label.setText(
            f"Board ready: size={board_size}, snakes={len(self._snake_heads)}, ladders={len(self._ladder_bases)}. "
            "Click Roll Dice once to start autoplay turns."
        )

    def on_roll_clicked(self):
        if self.game is None or self._auto_running:
            return

        self._auto_running = True
        self._next_actor = "Player"
        self.roll_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.status_label.setText("Autoplay started. Turns will play slowly with dice popups.")
        QTimer.singleShot(250, self._play_next_turn)

    def _play_next_turn(self):
        if not self._auto_running or self.game is None:
            return

        actor = self._next_actor
        roll = self.game.dice_roll()

        if actor == "Player":
            old_pos = self.game.player_position
            proposed = old_pos + roll
            new_pos = self.game.move(old_pos, roll)
            self.game.player_position = new_pos
        else:
            old_pos = self.game.bot_position
            proposed = old_pos + roll
            new_pos = self.game.move(old_pos, roll)
            self.game.bot_position = new_pos

        transition = "normal"
        if proposed > self.game.board_size - 1:
            transition = "overshoot"
        elif new_pos < proposed:
            transition = "snake"
        elif new_pos > proposed:
            transition = "ladder"

        self._show_dice_popup(actor, roll, old_pos, proposed, new_pos, transition)
        self._render_board()

        winner = self.game.check_winner()
        if winner:
            self._auto_running = False
            self.roll_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.status_label.setText(f"{winner} wins! Click New Game to play again.")
            QMessageBox.information(self, "Game Over", f"{winner} wins!")
            return

        self._next_actor = "Bot" if actor == "Player" else "Player"
        self.status_label.setText(
            f"Last turn: {actor} rolled {roll} and moved {old_pos} -> {new_pos}. "
            f"Next turn: {self._next_actor}."
        )
        QTimer.singleShot(self._turn_delay_ms, self._play_next_turn)

    def _show_dice_popup(self, actor, roll, old_pos, proposed, new_pos, transition):
        if transition == "snake":
            detail = f"Landed on a snake: {proposed} -> {new_pos}"
        elif transition == "ladder":
            detail = f"Climbed a ladder: {proposed} -> {new_pos}"
        elif transition == "overshoot":
            detail = f"Overshot END from {old_pos} with roll {roll}, stayed in place."
        else:
            detail = f"Moved from {old_pos} to {new_pos}."

        popup = QMessageBox(self)
        popup.setWindowTitle("Dice Roll")
        popup.setText(f"{actor} rolled a {roll}\n{detail}")
        popup.setStandardButtons(QMessageBox.NoButton)
        QTimer.singleShot(900, popup.accept)
        popup.exec_()

    def _extract_special_positions(self):
        self._snake_heads = {}
        self._ladder_bases = {}

        current = self.game.head if self.game else None
        while current is not None:
            if current.snake is not None:
                self._snake_heads[current.position] = current.snake.position
            if current.ladder is not None:
                self._ladder_bases[current.position] = current.ladder.position
            current = current.next

    def _clear_board_grid(self):
        while self.board_grid.count():
            item = self.board_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._board_labels.clear()

    def _build_board_cells(self):
        self._clear_board_grid()
        if self.game is None:
            return

        board_size = self.game.board_size
        self._columns = min(10, board_size)
        self._rows = ceil(board_size / self._columns)

        for position in range(board_size):
            cell = QLabel()
            cell.setAlignment(Qt.AlignCenter)
            cell.setWordWrap(True)
            cell.setMinimumSize(72, 56)
            cell.setFont(QFont("Arial", 9))
            cell.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            row, col = self._to_grid(position)
            self.board_grid.addWidget(cell, row, col)
            self._board_labels[position] = cell

        self._sync_overlay_geometry()

    def _to_grid(self, position):
        # Serpentine board flow from bottom row:
        # right, then up, then left, then up, repeating.
        row_from_bottom = position // self._columns
        row = self._rows - 1 - row_from_bottom

        index_in_row = position % self._columns
        if row_from_bottom % 2 == 0:
            col = index_in_row
        else:
            col = self._columns - 1 - index_in_row

        return row, col

    def _sync_overlay_geometry(self):
        if not hasattr(self, "board_overlay"):
            return
        self.board_overlay.setGeometry(self.board_widget.rect())
        self.board_overlay.raise_()
        self.board_overlay.update()

    def _cell_center(self, position):
        label = self._board_labels.get(position)
        if label is None:
            return None
        return label.geometry().center()

    def _cell_rect(self, position):
        label = self._board_labels.get(position)
        if label is None:
            return None
        return label.geometry()

    def _border_point_toward(self, rect, target_point):
        center = rect.center()
        cx = float(center.x())
        cy = float(center.y())
        tx = float(target_point.x())
        ty = float(target_point.y())

        dx = tx - cx
        dy = ty - cy
        if dx == 0 and dy == 0:
            return QPointF(cx, cy)

        half_w = rect.width() / 2.0
        half_h = rect.height() / 2.0
        scale_x = float("inf") if dx == 0 else half_w / abs(dx)
        scale_y = float("inf") if dy == 0 else half_h / abs(dy)
        scale = min(scale_x, scale_y)

        return QPointF(cx + dx * scale, cy + dy * scale)

    def _segment_between_cells(self, start_pos, end_pos):
        start_rect = self._cell_rect(start_pos)
        end_rect = self._cell_rect(end_pos)
        if start_rect is None or end_rect is None:
            return None, None

        end_center = QPointF(float(end_rect.center().x()), float(end_rect.center().y()))
        start_center = QPointF(float(start_rect.center().x()), float(start_rect.center().y()))

        p1 = self._border_point_toward(start_rect, end_center)
        p2 = self._border_point_toward(end_rect, start_center)
        return p1, p2

    def _render_board(self):
        if self.game is None:
            return

        last_position = self.game.board_size - 1
        player_pos = self.game.player_position
        bot_pos = self.game.bot_position

        for pos, label in self._board_labels.items():
            lines = [str(pos)]
            if pos == 0:
                lines.append("START")
            if pos == last_position:
                lines.append("END")
            if pos in self._snake_heads:
                lines.append(f"S->{self._snake_heads[pos]}")
            elif pos in self._ladder_bases:
                lines.append(f"L->{self._ladder_bases[pos]}")

            occupants = []
            if pos == player_pos:
                occupants.append("P")
            if pos == bot_pos:
                occupants.append("B")
            if occupants:
                lines.append("/".join(occupants))

            if pos in self._snake_heads:
                bg = "#ffd6d6"
            elif pos in self._ladder_bases:
                bg = "#d9f8dd"
            else:
                bg = "#f3f3f3"

            if pos == player_pos and pos == bot_pos:
                border = "3px solid #6f42c1"
            elif pos == player_pos:
                border = "3px solid #0d6efd"
            elif pos == bot_pos:
                border = "3px solid #ff8c00"
            else:
                border = "1px solid #9c9c9c"

            label.setText("\n".join(lines))
            label.setStyleSheet(
                f"background: {bg}; border: {border}; border-radius: 4px; padding: 2px;"
            )

        self._sync_overlay_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_overlay_geometry()


def _read_int_with_default(prompt, default, min_value):
    raw = input(f"{prompt} [{default}]: ").strip()
    if raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(min_value, value)


def run_cli_game():
    print("Snakes and Ladders (CLI)")
    board_size = _read_int_with_default("Board size", 100, 20)
    snakes = _read_int_with_default("Number of snakes", 10, 0)
    ladders = _read_int_with_default("Number of ladders", 10, 0)

    game = Snakes_And_Ladder(board_size=board_size, snakes=snakes, ladders=ladders)
    game.debug_print_board_v2()
    game.play_game()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli_game()
    else:
        app = QApplication([])
        window = SnLGUI()
        window.show()
        app.exec_()
