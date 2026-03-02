from PyQt5.QtWidgets import QApplication,QMessageBox, QInputDialog, QFrame,QSizePolicy, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget, QLineEdit, QHBoxLayout, QGridLayout, QLayout
from PyQt5.QtCore import Qt, QEvent, QPoint, QTimer
from PyQt5.QtGui import QFont, QPixmap, QKeySequence, QGuiApplication, QFontMetrics, QTextDocument
from PyQt5.QtWidgets import QShortcut

import random


class MainWindow(QWidget):
    _size_debug = False

    def __init__(self,):
        super().__init__()
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.setWindowTitle('Minesweeper')
        self.active_game_window = None
        

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        
        self.stacked_widget = QStackedWidget(self)
        self.welcome_screen = WelcomeScreen(self)

        self.stacked_widget.addWidget(self.welcome_screen)
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
        
        self.show_welcome_screen()

    def show_welcome_screen(self):
        # Return to the lightweight welcome UI and size the window to content.
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.layout().activate()
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    def _on_game_window_closed(self):
        # Called by the game window on close: restore the welcome screen window.
        self.active_game_window = None
        self.show_welcome_screen()
        self.show()
        self.raise_()
        self.activateWindow()

    def start_minesweeper_game(self, difficulty):
        # Main window owns game-window creation to keep navigation/state centralized.
        game_window = MinesweeperGameWindow(self, difficulty)
        self.active_game_window = game_window
        game_window.show()
        self.hide()

class CellButton(QPushButton):
    # Lightweight cell widget that knows its row/col and forwards clicks.
    def __init__(self, row, col, click_handler, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self._click_handler = click_handler

    def mousePressEvent(self, event):
        # Right click always means flag action; left click means reveal unless flag mode says otherwise.
        if event.button() == Qt.RightButton:
            self._click_handler(self.row, self.col, force_flag=True)
            return
        if event.button() == Qt.LeftButton:
            self._click_handler(self.row, self.col, force_flag=False)
            return
        super().mousePressEvent(event)

class MinesweeperGameWindow(QWidget):
    # Game window owns both the visual board and the active game state for one difficulty.
    def __init__(self, main_window : MainWindow, difficulty):
        super().__init__()
        self.main_window = main_window
        self.difficulty = difficulty
        # Model/state for current round.
        # MinesweeperGame precomputes a grid where -1 is a mine and 0..8 are neighbor counts.
        self.game = MinesweeperGame(difficulty)
        self.rows, self.cols = self.game.grid_size
        self.total_mines = self.game.num_mines
        # UI interaction state.
        # - flag_mode toggles left-click behavior
        # - flagged_cells tracks current flag placements
        # - revealed_cells tracks opened cells
        # - game_over blocks further actions after win/loss
        self.flag_mode = False
        self.flagged_cells = set()
        self.revealed_cells = set()
        self.game_over = False

        self.setWindowTitle("Minesweeper")
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._build_ui()
        self._build_grid()
        self._update_header()
        self.layout().activate()
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    def _build_ui(self):
        # Root container and spacing for a compact desktop-game look.
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Header row: flag mode toggle, mines-left counter, mood indicator.
        # Mood is driven by whether flags exceed the true bomb count.
        header = QHBoxLayout()
        header.setSpacing(8)

        self.flag_button = QPushButton("Flag Mode: OFF")
        self.flag_button.setCheckable(True)
        self.flag_button.clicked.connect(self._on_flag_mode_toggled)

        self.mine_counter_label = QLabel()
        self.mine_counter_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.mood_label = QLabel("🙂")
        self.mood_label.setFont(QFont("Arial", 18))
        self.mood_label.setAlignment(Qt.AlignCenter)
        self.mood_label.setFixedWidth(36)

        header.addWidget(self.flag_button)
        header.addStretch()
        header.addWidget(self.mine_counter_label)
        header.addWidget(self.mood_label)

        # Board host for the variable-size clickable grid.
        self.board_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.board_widget.setLayout(self.grid_layout)

        root.addLayout(header)
        root.addWidget(self.board_widget, alignment=Qt.AlignCenter)
        self.setLayout(root)

    def _build_grid(self):
        # Create one button per cell based on current difficulty dimensions.
        # The cell_buttons matrix mirrors the game.grid shape for direct row/col lookup.
        self.cell_buttons = []
        cell_size = 26
        for row in range(self.rows):
            row_buttons = []
            for col in range(self.cols):
                button = CellButton(row, col, self._on_cell_clicked)
                button.setFixedSize(cell_size, cell_size)
                button.setFocusPolicy(Qt.NoFocus)
                self.grid_layout.addWidget(button, row, col)
                row_buttons.append(button)
            self.cell_buttons.append(row_buttons)

    def _clear_grid(self):
        # Remove existing button widgets before rebuilding (used for restart).
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _restart_board(self):
        # Reinitialize model and UI state for the same selected difficulty.
        # This is used by win/loss dialogs when player chooses to restart immediately.
        self.game = MinesweeperGame(self.difficulty)
        self.rows, self.cols = self.game.grid_size
        self.total_mines = self.game.num_mines
        self.flag_mode = False
        self.flagged_cells = set()
        self.revealed_cells = set()
        self.game_over = False
        self.flag_button.setChecked(False)
        self.flag_button.setText("Flag Mode: OFF")

        self._clear_grid()
        self._build_grid()
        self._update_header()

        # Re-fit window to the rebuilt board in case dimensions differ.
        self.layout().activate()
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    def _on_flag_mode_toggled(self):
        # Flag mode lets left-click place/remove flags instead of revealing.
        self.flag_mode = self.flag_button.isChecked()
        self.flag_button.setText("Flag Mode: ON" if self.flag_mode else "Flag Mode: OFF")

    def _on_cell_clicked(self, row, col, force_flag=False):
        # Ignore input once round has ended.
        if self.game_over:
            return

        # Decide whether this click should flag or reveal.
        use_flag_action = force_flag or self.flag_mode
        if use_flag_action:
            self._toggle_flag(row, col)
            return

        if (row, col) in self.flagged_cells or (row, col) in self.revealed_cells:
            return

        if self.game.grid[row][col] == -1:
            # Opening a mine ends the round immediately.
            self._reveal_mine_and_end(row, col)
            return

        # Safe reveal path; may recursively/flood reveal neighbors.
        self._reveal_region(row, col)
        self._check_win_condition()

    def _toggle_flag(self, row, col):
        # Flags can only be changed on unrevealed cells.
        if (row, col) in self.revealed_cells:
            return
        button = self.cell_buttons[row][col]
        if (row, col) in self.flagged_cells:
            self.flagged_cells.remove((row, col))
            button.setText("")
        else:
            self.flagged_cells.add((row, col))
            button.setText("🚩")
        # Counter + mood update after each flag mutation.
        self._update_header()

    def _reveal_region(self, start_row, start_col):
        # Flood reveal using an explicit stack (iterative DFS/BFS-style).
        # Behavior matches classic Minesweeper:
        # - Numbered cells reveal only themselves.
        # - Zero cells reveal neighbors, which can cascade.
        stack = [(start_row, start_col)]
        while stack:
            row, col = stack.pop()
            # Skip invalid/blocked cells first.
            if (row, col) in self.revealed_cells or (row, col) in self.flagged_cells:
                continue
            if not (0 <= row < self.rows and 0 <= col < self.cols):
                continue
            if self.game.grid[row][col] == -1:
                continue

            # Mark as revealed and visually disable the button.
            self.revealed_cells.add((row, col))
            button = self.cell_buttons[row][col]
            button.setEnabled(False)
            button.setStyleSheet("background-color: #dcdcdc;")

            cell_value = self.game.grid[row][col]
            if cell_value > 0:
                # Numbered border cell: reveal number and stop expanding from here.
                button.setText(str(cell_value))
                continue

            # Zero-value cell: clear text and enqueue all neighbors.
            button.setText("")
            # d_row and d_col are RELATIVE offsets from the current cell.
            # Each can be -1, 0, or +1:
            #   -1 => one step up/left
            #    0 => same row/col
            #   +1 => one step down/right
            # Combining both loops gives a 3x3 neighborhood around (row, col).
            # Example: (d_row=-1, d_col=1) means top-right neighbor.
            # We skip (0,0) because that is the current cell itself.
            for d_row in (-1, 0, 1):
                for d_col in (-1, 0, 1):
                    if d_row == 0 and d_col == 0:
                        continue
                    next_row = row + d_row
                    next_col = col + d_col
                    # Bounds check keeps neighbors inside the board.
                    if 0 <= next_row < self.rows and 0 <= next_col < self.cols:
                        # Only enqueue cells we have not already revealed.
                        if (next_row, next_col) not in self.revealed_cells:
                            stack.append((next_row, next_col))

    def _reveal_mine_and_end(self, hit_row, hit_col):
        # Show all mines and lock board.
        # Then offer restart for the same difficulty.
        self.game_over = True
        for row in range(self.rows):
            for col in range(self.cols):
                button = self.cell_buttons[row][col]
                button.setEnabled(False)
                if self.game.grid[row][col] == -1:
                    button.setText("💣")
        self.cell_buttons[hit_row][hit_col].setStyleSheet("background-color: #f2a3a3;")
        answer = QMessageBox.question(
            self,
            "Minesweeper",
            "Boom! You hit a mine.\n\nRestart this board?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer == QMessageBox.Yes:
            self._restart_board()

    def _check_win_condition(self):
        # Player wins when all non-mine cells are revealed.
        # Flags are not required for win in this implementation.
        safe_cells = (self.rows * self.cols) - self.total_mines
        if len(self.revealed_cells) != safe_cells:
            return

        self.game_over = True
        for row in range(self.rows):
            for col in range(self.cols):
                self.cell_buttons[row][col].setEnabled(False)
        answer = QMessageBox.question(
            self,
            "Minesweeper",
            "You cleared the board!\n\nRestart this board?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer == QMessageBox.Yes:
            self._restart_board()

    def _update_header(self):
        # Header reflects flag pressure and remaining mine estimate.
        # mines_left can go negative if player over-flags; mood reflects that state.
        mines_left = self.total_mines - len(self.flagged_cells)
        self.mine_counter_label.setText(f"Mines Left: {mines_left}")
        self.mood_label.setText("☹️" if len(self.flagged_cells) > self.total_mines else "🙂")



    def closeEvent(self, event):
        super().closeEvent(event)
        self.main_window._on_game_window_closed()
        

class WelcomeScreen(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        title = QLabel("Welcome to Minesweeper!")
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setContentsMargins(6, 0, 6, 0)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.setLayout(layout)

        play_button = QPushButton("Play Minesweeper")
        play_button.setFont(QFont("Arial", 14))
        play_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        play_button.clicked.connect(self.start_game)
        layout.addWidget(play_button)

    def start_game(self):
        # Prompt difficulty, then delegate actual window creation to MainWindow.
        difficulty, ok = QInputDialog.getItem(self, "Select Difficulty", "Choose difficulty level:", ["Easy", "Medium", "Hard"], 0, False)
        if not ok:
            return
        self.main_window.start_minesweeper_game(difficulty)



class MinesweeperGame:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        # Configure board dimensions and mine count by difficulty.
        if difficulty == "Easy":
            self.grid_size = (9, 9)
            self.num_mines = 10
        elif difficulty == "Medium":
            self.grid_size = (16, 16)
            self.num_mines = 40
        elif difficulty == "Hard":
            self.grid_size = (30, 30)
            self.num_mines = 99
        # grid holds final values used by UI: mine=-1, otherwise neighbor count.
        self.grid = self.create_grid()
    
    def debug_print_grid(self):
        for row in self.grid:
            print(' '.join(str(cell) for cell in row))
    
    def create_grid(self):
        # Step 1: build empty grid.
        grid = [[0 for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
        
        # Step 2: randomly place mines.
        for _ in range(self.num_mines):
            while True:
                x = random.randint(0, self.grid_size[0] - 1)
                y = random.randint(0, self.grid_size[1] - 1)
                if grid[x][y] == 0:  # Place mine if cell is empty
                    grid[x][y] = -1  # -1 represents a mine
                    break
        # Step 3: for every non-mine cell, compute adjacent mine counts.
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                if grid[x][y] == -1:
                    continue
                count = 0
                # Same neighbor-offset idea as reveal logic:
                # dx/dy in (-1,0,1) scans all adjacent positions around (x,y).
                # This includes diagonals, which is standard Minesweeper behavior.
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.grid_size[0] and 0 <= ny < self.grid_size[1]:
                            if grid[nx][ny] == -1:
                                count += 1
                grid[x][y] = count
        return grid





if __name__ == "__main__":
    #game=MinesweeperGame("Medium")
    #game.debug_print_grid()
    
    
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()