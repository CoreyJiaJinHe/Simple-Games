from PyQt5.QtWidgets import QApplication,QMessageBox, QInputDialog, QFrame,QSizePolicy, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget, QLineEdit, QHBoxLayout, QGridLayout, QLayout
from PyQt5.QtCore import Qt, QEvent, QPoint, QTimer
from PyQt5.QtGui import QFont, QPixmap, QKeySequence, QGuiApplication, QFontMetrics, QTextDocument
from PyQt5.QtWidgets import QShortcut

from game import Poker_for_GUI as PokerGame
from Five_Card_Poker import FiveCardPoker
from blackjack import BlackJack as BlackjackGame
from game import Database_Helper as DBHelper
BLACKJACK_DEBUG_EXPAND_WINDOW = False

class MainWindow(QWidget):
    def __init__(self,):
        super().__init__()
        self.setWindowTitle('Card Games')
        
        # Border frames restored to prior version
        self.outer_frame = QFrame(self)
        self.outer_frame.setStyleSheet("background: transparent; border: 8px solid red; border-radius: 30px;")
        self.outer_frame.setGeometry(self.rect())
        self.outer_frame.lower()
        self.outer_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet("background: transparent; border: 8px solid black; border-radius: 22px;")
        self.middle_frame.setGeometry(self.rect().adjusted(8, 8, 0, 0))
        self.middle_frame.lower()
        self.middle_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.outer_frame.hide()
        self.middle_frame.hide()

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        
        self.stacked_widget = QStackedWidget(self)
        self.welcome_screen = WelcomeScreen(
            poker_callback=self.show_poker_game_screen,
            blackjack_callback=self.show_blackjack_game_screen,
            five_card_poker_callback=self.show_five_card_poker_game_screen
        )
        self.poker_game_screen = PokerGameScreen(parent=self)
        self.five_card_poker_game_screen = FiveCardPokerGameScreen(parent=self)
        self.blackjack_game_screen = BlackjackGameScreen(parent=self)

        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.poker_game_screen)
        self.stacked_widget.addWidget(self.five_card_poker_game_screen)
        self.stacked_widget.addWidget(self.blackjack_game_screen)
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
        
        self.show_welcome_screen()

    def show_welcome_screen(self):
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        # Hide outer frames
        self.outer_frame.hide()
        self.middle_frame.hide()
        # Set a small fixed size for the welcome screen
        self.setMinimumSize(0, 0)
        self.setMaximumSize(600, 600)
        self.resize(420, 320)
        self.setFixedSize(420, 320)
        
    def show_blackjack_game_screen(self, player_name="You", bot_count=2):
        print(f"Starting Blackjack game for {player_name} with {bot_count} bots")
        # You can prompt for player name and bot count here if needed
        self.stacked_widget.setCurrentWidget(self.blackjack_game_screen)
        self.outer_frame.show()
        self.middle_frame.show()
        self.blackjack_game_screen.set_bot_count(bot_count)
        self.blackjack_game_screen.set_player_name(player_name)
        self.blackjack_game_screen.start_game()
        # Remove fixed size and resize to fit game content
        self.setFixedSize(0, 0)
        if not BLACKJACK_DEBUG_EXPAND_WINDOW:
            # Lock a reasonable minimum size based on the initial
            # layout so cards don't get squished.
            try:
                self.setMinimumSize(self.blackjack_game_screen.sizeHint())
            except Exception:
                pass
            # Fit window to content after screen switch
            self.adjustSize()
            # Start at the computed minimum size automatically
            try:
                self.resize(self.minimumSize())
            except Exception:
                pass
        else:
            # In debug/override mode, just let Qt choose an
            # appropriate size and allow the window to grow as
            # more content is added.
            self.adjustSize()
        
        
    def show_poker_game_screen(self, player_name="You", bot_count=2):
        print(f"Starting Poker game for {player_name} vs {bot_count} bots")
        self.poker_game_screen.set_player_name(player_name)
        self.poker_game_screen.set_bot_count(bot_count)
        self.stacked_widget.setCurrentWidget(self.poker_game_screen)
        # Outermost border (red)
        self.outer_frame.show()
        # Middle border (black)
        self.middle_frame.show()
        # Remove fixed size and resize to fit game content based on initial layout
        self.setFixedSize(0, 0)
        try:
            self.setMinimumSize(self.poker_game_screen.sizeHint())
        except Exception:
            pass
        self.adjustSize()
        try:
            self.resize(self.minimumSize())
        except Exception:
            pass
        # Now start the game; later card additions won't shrink the window
        # below the size needed for all five dealer/community cards.
        self.poker_game_screen.start_game()
        # Let Qt compute an appropriate initial size based on content
        self.adjustSize()

    def show_five_card_poker_game_screen(self, player_name="You", bot_count=3):
        print(f"Starting Five Card Poker game for {player_name} vs {bot_count} bots")
        self.five_card_poker_game_screen.set_player_name(player_name)
        self.five_card_poker_game_screen.set_bot_count(bot_count)
        self.stacked_widget.setCurrentWidget(self.five_card_poker_game_screen)
        # Show borders
        self.outer_frame.show()
        self.middle_frame.show()
        # Remove fixed size and resize to fit content
        self.setFixedSize(0, 0)
        try:
            self.setMinimumSize(self.five_card_poker_game_screen.sizeHint())
        except Exception:
            pass
        self.adjustSize()
        try:
            self.resize(self.minimumSize())
        except Exception:
            pass
        self.five_card_poker_game_screen.start_game()
        self.adjustSize()
    def resizeEvent(self, event):
        # Ensure the background frames fill the window
        self.outer_frame.setGeometry(self.rect())
        self.middle_frame.setGeometry(self.rect().adjusted(8, 8, -8, -8))
        super().resizeEvent(event)





class FiveCardPokerGameScreen(QWidget):
    class ClickableLabel(QLabel):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.selected = False
        def mousePressEvent(self, event):
            self.selected = not self.selected
            self.update_selection_style()
            if hasattr(self.parent(), 'on_card_clicked'):
                try:
                    self.parent().on_card_clicked(self)
                except Exception:
                    pass
        def update_selection_style(self):
            if self.selected:
                self.setStyleSheet("border: 2px solid gold;")
            else:
                self.setStyleSheet("")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.bot_count = 3
        self.player_name = None
        self.engine = None
        self._selected_indices = set()
        self._pending_to_call = 0
        self._discard_submit_requested = False

        layout = QVBoxLayout()

        # Top bar
        self.wallet_label = QLabel("Wallet: $1000")
        self.wallet_label.setFont(QFont('Arial', 14))
        self.wallet_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.wallet_label)
        layout.addLayout(top_bar_layout)

        # Table area grid: Up (top center), Left, Right, Down (user)
        table_area = QGridLayout()
        table_area.setColumnStretch(0, 1)
        table_area.setColumnStretch(1, 2)
        table_area.setColumnStretch(2, 1)
        table_area.setRowStretch(0, 1)
        table_area.setRowStretch(1, 0)
        table_area.setRowStretch(2, 1)

        # Create player widgets
        
        
        self.opponent_widgets = []
        for i in range(3):
            opp = self.create_opponent_widget(f"Bot {i+1}")
            self.opponent_widgets.append(opp)
            
        self.player_widget = self.create_player_widget(self.player_name)

        # Place them
        table_area.addWidget(self.opponent_widgets[0], 0, 1, alignment=Qt.AlignCenter)
        table_area.addWidget(self.opponent_widgets[1], 1, 0, alignment=Qt.AlignLeft)
        table_area.addWidget(self.opponent_widgets[2], 1, 2, alignment=Qt.AlignRight)
        table_area.addWidget(self.player_widget, 2, 1, alignment=Qt.AlignCenter)

        # Center column: pot + chips only
        center_col_layout = QVBoxLayout()
        center_col_layout.setAlignment(Qt.AlignCenter)
        self.pot_label = QLabel("Pot: 0")
        self.pot_label.setFont(QFont('Arial', 14))
        self.pot_label.setAlignment(Qt.AlignCenter)
        self.chips_widget = QLabel("CHIPS PLACEHOLDER")
        self.chips_widget.setMinimumSize(200, 40)
        self.chips_widget.setStyleSheet("background: #bbb; border: 2px solid #888; border-radius: 8px;")

        center_col_layout.addWidget(self.pot_label, alignment=Qt.AlignCenter)
        center_col_layout.addSpacing(8)
        center_col_layout.addWidget(self.chips_widget, alignment=Qt.AlignCenter)

        center_col_widget = QWidget()
        center_col_widget.setLayout(center_col_layout)
        table_area.addWidget(center_col_widget, 1, 1, alignment=Qt.AlignCenter)

        # Controls panel (NOT centered in table)
        controls_layout = QVBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)
        self.game_phase_label = QLabel("Phase: ")
        self.game_phase_label.setFont(QFont('Arial', 16))

        # Bet input
        self.bet_input = QLineEdit(self)
        self.bet_input.setPlaceholderText("Amount")
        self.bet_input.setFixedWidth(120)
        self.bet_button = QPushButton("Place Bet", self)
        self.bet_button.setFixedWidth(100)
        self.bet_button.clicked.connect(self.on_bet_submitted)

        # Discard controls
        self.discard_button = QPushButton("Discard Selected", self)
        self.discard_button.setFixedWidth(140)
        self.discard_button.clicked.connect(self.on_discard_clicked)

        controls_layout.addWidget(self.game_phase_label, alignment=Qt.AlignCenter)
        controls_layout.addSpacing(6)
        bet_row = QHBoxLayout()
        bet_row.addWidget(QLabel("Enter your bet:"))
        bet_row.addWidget(self.bet_input)
        bet_row.addWidget(self.bet_button)
        controls_layout.addLayout(bet_row)
        controls_layout.addSpacing(8)
        
        self.bet_error_label = QLabel("")
        self.bet_error_label.setStyleSheet("color: red;")
        controls_layout.addWidget(self.bet_error_label, alignment=Qt.AlignCenter)
        
        controls_layout.addWidget(self.discard_button, alignment=Qt.AlignCenter)

        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        layout.addLayout(table_area)
        layout.addWidget(controls_widget, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def create_opponent_widget(self, name):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 16))
        vbox.addWidget(name_label, alignment=Qt.AlignCenter)
        hand_layout = QHBoxLayout()
        hand_layout.setSpacing(4)
        labels = []
        for i in range(5):
            lbl = QLabel(self)
            lbl.setFixedSize(80, 120)
            pix = QPixmap("cards_graphic/card_back.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl.setPixmap(pix)
            hand_layout.addWidget(lbl)
            labels.append(lbl)
        vbox.addLayout(hand_layout)
        bet_label = QLabel("Bet: 0")
        bet_label.setFont(QFont('Arial', 12))
        bet_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(bet_label, alignment=Qt.AlignCenter)
        widget.setLayout(vbox)
        widget.name_label = name_label
        widget.card_labels = labels
        widget.bet_label = bet_label
        return widget

    def create_player_widget(self, name):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 16))
        vbox.addWidget(name_label, alignment=Qt.AlignCenter)
        hand_layout = QHBoxLayout()
        hand_layout.setSpacing(4)
        labels = []
        for i in range(5):
            lbl = FiveCardPokerGameScreen.ClickableLabel(self)
            lbl.setFixedSize(80, 120)
            pix = QPixmap("cards_graphic/card_back.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl.setPixmap(pix)
            hand_layout.addWidget(lbl)
            labels.append(lbl)
        vbox.addLayout(hand_layout)
        bet_label = QLabel("Bet: 0")
        bet_label.setFont(QFont('Arial', 12))
        bet_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(bet_label, alignment=Qt.AlignCenter)
        widget.setLayout(vbox)
        widget.name_label = name_label
        widget.card_labels = labels
        widget.bet_label = bet_label
        self.user_card_labels = labels
        return widget

    def set_player_name(self, player_name):
        self.player_name = player_name
        try:
            self.player_widget.name_label.setText(player_name)
        except Exception:
            pass

    def update_opponents(self, num_opponents):
        # Hide all first
        for opp in self.opponent_widgets:
            opp.hide()
        for i in range(num_opponents):
            self.opponent_widgets[i].show()
    
    def set_bot_count(self, bot_count):
        # Fixed to 3 bots for four players total
        self.bot_count = max(0, min(3, bot_count))
        self.update_opponents(bot_count)

    def start_game(self):
        player_names = [self.player_name] + [f"Bot{i}" for i in range(1, self.bot_count + 1)]
        # Pad/trim bot names to 3
        bot_names = (player_names[1:4])
        player_names = [self.player_name] + bot_names
        self.engine = FiveCardPoker(
            player_names,
            action_callback=self.on_action_requested,
            phase_callback=self.on_phase,
            pot_update_callback=self.update_pot,
            bot_bet_update_callback=self.update_bot_bet,
            bot_fold_callback=self.on_bot_fold,
        )
        self.engine.start_game()

    def on_card_clicked(self, label):
        # Maintain selection up to 3 cards; deselect oldest if >3
        try:
            idx = self.user_card_labels.index(label)
        except ValueError:
            return
        if label.selected:
            self._selected_indices.add(idx)
            if len(self._selected_indices) > 3:
                # Deselect the earliest selected
                first_idx = next(iter(self._selected_indices))
                self._selected_indices.remove(first_idx)
                lbl = self.user_card_labels[first_idx]
                if isinstance(lbl, FiveCardPokerGameScreen.ClickableLabel):
                    lbl.selected = False
                    lbl.update_selection_style()
        else:
            self._selected_indices.discard(idx)

    def update_pot(self, amount):
        self.pot_label.setText(f"Pot: {amount}")

    def update_bot_bet(self, bot_index, amount):
        # bot_index: 0 for Bot1, 1 for Bot2, 2 for Bot3
        try:
            targets = [self.opponent_widgets[0], self.opponent_widgets[1], self.opponent_widgets[2]]
            if 0 <= bot_index < len(targets):
                targets[bot_index].bet_label.setText(f"Bet: {amount}")
        except Exception:
            pass

    def on_bot_fold(self, bot_index, hand):
        try:
            targets = [self.opponent_widgets[0], self.opponent_widgets[1], self.opponent_widgets[2]]
            wid = targets[bot_index]
            wid.bet_label.setText("Folded")
            # Reveal first two cards for flavor
            for i, card in enumerate(hand[:2]):
                pix = QPixmap(f"cards_graphic/{card}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                wid.card_labels[i].setPixmap(pix)
        except Exception:
            pass

    def on_phase(self, phase, *args):
        print(f"Phase update: {phase}, args: {args}")
        if phase =="update_initial_hands":
            players = args[0]
            self.render_all_hands(players)
        # Update game_phase label and hands based on phase
        self.game_phase_label.setText(f"Phase: {phase}")
        if phase == "update_hands" and args:
            players = args[0]
            self.render_all_hands(players)
        elif phase == "winner" and args:
            # args: [winner_names, winning_hand, pot]
            pass

    def render_all_hands(self, players):
        # Map players to widgets: assume names order [You, Bot1, Bot2, Bot3]
        try:
            by_name = {p.name: p for p in players}
            # User
            print(f"Rendering hand for player: {self.player_name}")
            self.render_hand_to_widget(self.player_widget, by_name.get(self.player_name))
            # Bots (Bot1 -> top, Bot2 -> left, Bot3 -> right)
            for idx, wid_name in enumerate(["Bot1", "Bot2", "Bot3"]):
                if idx < len(self.opponent_widgets):
                    self.render_hand_to_widget(self.opponent_widgets[idx], by_name.get(wid_name))
        except Exception:
            pass

    def render_hand_to_widget(self, widget, player):
        labels = getattr(widget, 'card_labels', [])
        hand = player.hand if player and hasattr(player, 'hand') else []
        print (hand)
        for i, lbl in enumerate(labels):
            if i < len(hand):
                card = hand[i]
                pix = QPixmap(f"cards_graphic/{card}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl.setPixmap(pix)
            else:
                back = QPixmap("cards_graphic/card_back.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl.setPixmap(back)

    def on_action_requested(self, action, payload=None):
        payload = payload or {}
        if action == "cards_to_discard_phase":
            max_to_discard = int(payload.get("max_to_discard", 3))
            self.game_phase_label.setText("Phase: Select up to 3 cards and click Discard")
            if not self._discard_submit_requested:
                return None
            
            indices = sorted(list(self._selected_indices))[:max_to_discard]
            # Clear selection after providing indices
            for idx in list(self._selected_indices):
                lbl = self.user_card_labels[idx]
                if isinstance(lbl, FiveCardPokerGameScreen.ClickableLabel):
                    lbl.selected = False
                    lbl.update_selection_style()
            self._selected_indices.clear()
            self._discard_submit_requested = False
            return indices
        elif action == "to_call":
            to_call = int(payload.get("to_call", 0))
            self._pending_to_call = int(to_call)
            self.game_phase_label.setText(f"Phase: To call {to_call}. Enter bet and Place Bet")
            # Return nothing; we'll resume later via betting_run
            return None
        return None

    def on_bet_submitted(self, minimum_bet=10):
        # Resume betting by updating the current human player's bet
        player = self.engine.players[0]  # Assuming player 0 is the human
        
        try:
            amount = int(self.bet_input.text())
        except ValueError:
            self.bet_error_label.setText("Please enter a valid number.")
            return
        
        if amount < minimum_bet:
            self.bet_error_label.setText(f"Bet must be at least {minimum_bet}.")
            return
        if amount > player.wallet:
            self.bet_error_label.setText("You do not have enough funds.")
            return
        if amount < 0:
            self.bet_error_label.setText("Bet must be positive.")
            return
        
        # Adjust bet via add_bet
        player.add_to_bet(amount)
        #self.disable_betting_buttons()
        self.wallet = player.wallet  # Update internal GUI wallet value
        #self.update_wallet(self.wallet)
        # Continue betting loop
        self.engine.betting_run()
    def on_discard_clicked(self):
        # Resume discard flow once user has selected desired cards.
        self._discard_submit_requested = True
        self.game_phase_label.setText("Phase: Discarding selected cards...")
        try:
            if self.engine is not None and hasattr(self.engine, "resume_discard_phase"):
                self.engine.resume_discard_phase()
            self.game_phase_label.setText("Phase: Dealing new cards...")
        except Exception:
            pass
    
    

class BlackjackGameScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window=parent
        self._prompted_this_round = False
        content_layout = QVBoxLayout()
        
        self.bot_count=5
        
        # --- Inner poker table (green) ---
        self.bg_frame = QFrame(self)
        self.bg_frame.setStyleSheet("background-color: #357a38; border-radius: 14px;")
        self.bg_frame.setGeometry(self.rect())
        self.bg_frame.lower()
        # Background overlay should not drive layout sizing
        self.bg_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.bg_frame.show()
        
        # --------------------------
        # --- Horizontal top bar ---
        self.wallet_label = QLabel("Wallet: $1000")  # Example starting value
        self.wallet_label.setFont(QFont('Arial', 14))
        self.wallet_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.wallet_label)

        content_layout.addLayout(top_bar_layout)
        
        # --- Bet label and input above cards ---
        self.bet_label = QLabel("Enter your bet:", self)
        self.bet_label.setFont(QFont('Arial', 16))

        self.bet_input = QLineEdit(self)
        self.bet_input.setPlaceholderText("Amount")
        self.bet_input.setFixedWidth(100)

        bet_input_layout = QHBoxLayout()
        bet_input_layout.addWidget(self.bet_label)
        bet_input_layout.addWidget(self.bet_input)
        self.initial_bet_button = QPushButton("Place Bet", self)
        bet_input_layout.addWidget(self.initial_bet_button)
        self.initial_bet_button.clicked.connect(self.on_initial_bet)

        self.bet_error_label = QLabel("")
        self.bet_error_label.setStyleSheet("color: red;")
        
        bet_input_vlayout = QVBoxLayout()
        bet_input_vlayout.addLayout(bet_input_layout)
        bet_input_vlayout.addWidget(self.bet_error_label, alignment=Qt.AlignCenter)
        bet_input_widget = QWidget()
        bet_input_widget.setLayout(bet_input_vlayout)
        
        
        # # --- Player cards ---
        # Use a grid so that up to four hands can be arranged
        # in two rows: hands 0-1 on the first row, 2-3 on the
        # second row.
        self.hands_layout = QGridLayout()
        self.hand_card_labels = []  # List of lists: one list of QLabel per hand

        # For debugging: set initial hands
        #self.set_hands([["AS", "10H"], ["8D", "3C", "7S"], ["4H", "5D"]])  # Example: three hands

        # --- Betting buttons stacked vertically ---
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        self.hit_button = QPushButton("Hit", self)
        self.hit_button.setFixedWidth(90)
        self.stand_button = QPushButton("Stand", self)
        self.stand_button.setFixedWidth(90)
        self.double_down_button = QPushButton("Double Down", self)
        self.double_down_button.setFixedWidth(90)
        self.surrender_button = QPushButton("Surrender", self)
        self.surrender_button.setFixedWidth(90)
        self.split_button = QPushButton("Split", self)
        self.split_button.setFixedWidth(90)
        buttons_layout.addWidget(self.hit_button)
        buttons_layout.addWidget(self.stand_button)
        buttons_layout.addWidget(self.double_down_button)
        buttons_layout.addWidget(self.surrender_button)
        buttons_layout.addWidget(self.split_button)
        self.hit_button.clicked.connect(lambda: self.on_action_button_clicked('hit'))
        self.stand_button.clicked.connect(lambda: self.on_action_button_clicked('stand'))
        self.double_down_button.clicked.connect(lambda: self.on_action_button_clicked('double_down'))
        self.surrender_button.clicked.connect(lambda: self.on_action_button_clicked('surrender'))
        self.split_button.clicked.connect(lambda: self.on_action_button_clicked('split'))
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        # Keep the button column from stretching vertically and
        # reduce downward shifting when extra hand rows appear.
        buttons_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # ---------------------
        # # Create placeholders for up to 5 opponents
        self.opponent_widgets = []
        for i in range(5):
            opp = self.create_opponent_widget(f"Bot {i+1}")
            self.opponent_widgets.append(opp)
        
        # --- Table area with grid layout ---
        table_area = QGridLayout()
        table_area.setColumnStretch(0, 1)
        # Widen the center column so overlay messages have more width
        table_area.setColumnStretch(1, 2)
        table_area.setColumnStretch(2, 1)
        table_area.setRowStretch(0, 1)
        table_area.setRowStretch(1, 0)
        table_area.setRowStretch(2, 1)

        # Top opponent (centered)
        table_area.addWidget(self.opponent_widgets[0], 0, 1, alignment=Qt.AlignCenter)
        # Left opponent
        table_area.addWidget(self.opponent_widgets[1], 1, 0, alignment=Qt.AlignLeft)
        # Right opponent
        table_area.addWidget(self.opponent_widgets[2], 1, 2, alignment=Qt.AlignRight)
        # Bottom left opponent
        table_area.addWidget(self.opponent_widgets[3], 2, 0, alignment=Qt.AlignLeft)
        # Bottom right opponent
        table_area.addWidget(self.opponent_widgets[4], 2, 2, alignment=Qt.AlignRight)
        # Table cards (center)
        self.table_cards_widget = QWidget()
        table_cards_layout = QHBoxLayout()
        table_cards_layout.setContentsMargins(0, 0, 0, 0)
        table_cards_layout.setSpacing(4)
        self.table_card_labels = []
        # # Create placeholders for up to 5 opponents
        self.dealer_widget = self.create_dealer_widget()
        table_cards_layout.addWidget(self.dealer_widget)
        self.table_cards_widget.setLayout(table_cards_layout)
        
        content_layout.addLayout(table_area)
        # --- Center column: stack table cards, pot label, chips widget ---
        center_col_layout = QVBoxLayout()
        center_col_layout.setAlignment(Qt.AlignCenter)
        self.chips_widget = QLabel("CHIPS PLACEHOLDER")
        self.chips_widget.setMinimumSize(200, 40)
        self.chips_widget.setStyleSheet("background: #bbb; border: 2px solid #888; border-radius: 8px;")
        
        # Center column layout
        center_col_layout.addSpacing(32)
        center_col_layout.addWidget(self.table_cards_widget, alignment=Qt.AlignCenter)
        center_col_layout.addSpacing(16)
        center_col_layout.addSpacing(16)
        center_col_layout.addWidget(self.chips_widget, alignment=Qt.AlignCenter)

        # Use an attribute so we can overlay the round message inside it without changing layout
        self.center_col_widget = QWidget()
        # Ensure the center column expands to fill its grid cell horizontally
        self.center_col_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.center_col_widget.setLayout(center_col_layout)
        table_area.addWidget(self.center_col_widget, 1, 1, alignment=Qt.AlignCenter)
        # --- Round message overlay (non-pushing, reparented to screen) ---
        self.round_message_label = QLabel("")
        # Reparent to the BlackjackGameScreen so we can size/place relative to the full content area
        self.round_message_label.setParent(self)
        self.round_message_label.setAlignment(Qt.AlignCenter)
        self.round_message_label.setFont(QFont('Arial', 18))
        self.round_message_label.setStyleSheet("color: #111; background: rgba(255,255,255,0.85); border: 1px solid #888; border-radius: 6px; padding: 2px 10px;")
        self.round_message_label.setWordWrap(True)
        # Let position_round_message compute width dynamically per content (no fixed min width)
        self.round_message_label.hide()
        
        # --- Combine cards and buttons horizontally ---
        cards_and_buttons_layout = QHBoxLayout()
        cards_and_buttons_layout.setContentsMargins(0, 0, 0, 0)
        cards_and_buttons_layout.setSpacing(20)
        hands_widget = QWidget()
        hands_widget.setLayout(self.hands_layout)
        cards_and_buttons_layout.addWidget(hands_widget)
        cards_and_buttons_layout.addSpacing(20)
        # Keep the buttons column top-aligned so it does not
        # move downward when additional hand rows appear.
        cards_and_buttons_layout.addWidget(buttons_widget, alignment=Qt.AlignTop)
        cards_and_buttons_widget = QWidget()
        cards_and_buttons_widget.setLayout(cards_and_buttons_layout)
        
        
        
        self.pot_label = QLabel("Pot: 0")
        self.pot_label.setFont(QFont('Arial',14))
        self.pot_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.pot_label, alignment=Qt.AlignCenter)
        
        # --- Add to main layout ---
        content_layout.addWidget(bet_input_widget, alignment=Qt.AlignCenter)
        self.hand_total_label = QLabel("Hand: ")
        self.hand_total_label.setFont(QFont('Arial', 14))
        #self.hand_total_label.setStyleSheet("color: #222;")
        content_layout.addWidget(self.hand_total_label, alignment=Qt.AlignCenter)
        # Keep the cards+buttons row centered vertically while the
        # buttons column itself stays top-aligned within that row.
        content_layout.addWidget(cards_and_buttons_widget, alignment=Qt.AlignCenter)

        # Prevent squishing: enforce minimum size equal to layout's size hint
        content_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.setLayout(content_layout)

        if not BLACKJACK_DEBUG_EXPAND_WINDOW:
            try:
                self.setMinimumSize(self.sizeHint())
            except Exception:
                pass

        # Local override: when True, leave all bot card slots
        # visible so the initial window size clearly reflects the
        # maximum layout requirements. When False (default), hide
        # all but the first two slots so the UI looks normal.
        show_all_bot_slots_for_debug = True
        # Expose for use in update_opponent_hand so we can
        # optionally keep all bot card slots visible.
        self._debug_show_all_bot_slots = show_all_bot_slots_for_debug
        try:
            for opp in getattr(self, "opponent_widgets", []):
                labels = getattr(opp, "card_labels", [])
                if show_all_bot_slots_for_debug:
                    for lbl in labels:
                        lbl.show()
                else:
                    for i, lbl in enumerate(labels):
                        if i < 2:
                            lbl.show()
                        else:
                            lbl.hide()
        except Exception:
            pass
        
        self.db_helper=DBHelper()
        # Round-state flags
        self.had_push_this_round = False
        self.dealer_blackjack_round = False
        
    def resizeEvent(self, event):
        # Ensure the background frame always fills the PokerGameScreen
        self.bg_frame.setGeometry(self.rect())
        # Keep round message overlay positioned within center column
        try:
            self.position_round_message()
        except Exception:
            pass
        super().resizeEvent(event)
    def set_hands(self, hands, active_hand_index=0):
        # Enforce a hard limit of four hands
        hands = hands[:4]
        # Clear old hand layouts and labels
        while self.hands_layout.count():
            item = self.hands_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.hand_card_labels = []

        total_hands = len(hands)
        # Base player card size
        base_w, base_h = 80, 120

        for idx, hand in enumerate(hands):
            # Dynamically scale card size and spacing:
            # - 1-2 cards: full size (possibly shrunk if many hands)
            # - 3-5 cards: shrink to fit within a max width
            # - 6+ cards: keep size as for 5 cards but overlap
            #   cards to the right so the hand doesn't grow
            #   indefinitely wide.
            n = len(hand)
            if n <= 0:
                n = 1

            if n <= 2:
                card_w, card_h = base_w, base_h
                spacing = 4
            elif 3 <= n <= 5:
                max_total_width = 400
                scale = min(1.0, max_total_width / float(n * base_w))
                card_w = max(35, int(base_w * scale))
                card_h = max(55, int(base_h * scale))
                spacing = 4
            else:
                # 6 or more cards: size them as if there were 5,
                # then overlap to the right.
                max_total_width = 400
                n_for_size = 5
                scale = min(1.0, max_total_width / float(n_for_size * base_w))
                card_w = max(35, int(base_w * scale))
                card_h = max(55, int(base_h * scale))
                overlap_fraction = 0.75  # right card covers 3/4 of left
                spacing = -int(card_w * overlap_fraction)

            # If we have more than two hands (i.e., a second row),
            # apply an additional scale-down so that all rows fit
            # comfortably without forcing the buttons far downward.
            if total_hands > 2:
                row_scale = 0.85
                card_w = max(30, int(card_w * row_scale))
                card_h = max(50, int(card_h * row_scale))

            hand_layout = QHBoxLayout()
            hand_layout.setSpacing(spacing)
            hand_labels = []
            for card in hand:
                card_label = QLabel(self)
                card_label.setFixedSize(card_w, card_h)
                pixmap = QPixmap(f"cards_graphic/{card}.png").scaled(card_w, card_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                card_label.setPixmap(pixmap)
                # Optionally highlight the active hand
                if idx == active_hand_index:
                    card_label.setStyleSheet("border: 2px solid gold;")
                else:
                    card_label.setStyleSheet("")
                hand_layout.addWidget(card_label)
                hand_labels.append(card_label)
            self.hand_card_labels.append(hand_labels)
            hand_widget = QWidget()
            hand_widget.setLayout(hand_layout)
            # Place hands 0-1 on the first row, 2-3 on the second
            row = 0 if idx < 2 else 1
            col = idx if idx < 2 else idx - 2
            self.hands_layout.addWidget(hand_widget, row, col, alignment=Qt.AlignCenter)

        # In override mode, let the main window resize itself
        # to accommodate larger layouts when additional hands
        # or many cards are present.
        if getattr(self, "main_window", None) is not None:
            try:
                if BLACKJACK_DEBUG_EXPAND_WINDOW:
                    self.main_window.adjustSize()
            except Exception:
                pass

    def create_opponent_widget(self, name, num_cards=2):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 16))
        # Two-layout hand: when there are more than 5 cards, the first layout holds the overlapped cards (using
        # negative spacing) and the second layout holds the final card without negative spacing. There is no
        # spacing or margin between these two layouts so they appear as one continuous hand.
        max_total_width = 300
        base_w, base_h = 60, 90

        cards_container = QWidget()
        outer_layout = QHBoxLayout(cards_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Use two inner layouts (rather than extra widgets) so Qt only has to manage layouts inside the fixed-width
        # container. The left layout holds the overlapped group; the right layout holds just the final card.
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        last_layout = QHBoxLayout()
        last_layout.setContentsMargins(0, 0, 0, 0)
        last_layout.setSpacing(0)

        outer_layout.addLayout(left_layout)
        outer_layout.addLayout(last_layout)
        outer_layout.setStretch(0, 1)
        outer_layout.setStretch(1, 0)
        cards_container.setFixedWidth(max_total_width)
        cards_container.setMinimumHeight(base_h)

        # Pre-create eleven card labels and lay them out once here
        # so the initial debug view shows all slots.
        card_labels = []
        for _ in range(11):
            card_label = QLabel(cards_container)
            card_label.setFixedSize(base_w, base_h)
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(base_w, base_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            card_labels.append(card_label)

        # Arrange the initial 11 cards as an overlapped "max hand"
        # so the window's size hint and debug view reflect the worst-case bot hand width.
        visible_n = len(card_labels)
        n_for_size = 5
        scale = min(1.0, max_total_width / float(n_for_size * base_w))
        card_w = max(30, int(base_w * scale))
        card_h = max(45, int(base_h * scale))
        overlap_fraction = 0.75
        spacing = -int(card_w * overlap_fraction)
        left_layout.setSpacing(spacing)

        for idx, lbl in enumerate(card_labels):
            lbl.setFixedSize(card_w, card_h)
            lbl.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(card_w, card_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            if idx < visible_n - 1:
                left_layout.addWidget(lbl)
            else:
                last_layout.addWidget(lbl)

        vbox.addWidget(name_label, alignment=Qt.AlignCenter)
        vbox.addWidget(cards_container, alignment=Qt.AlignCenter)
        bet_label = QLabel("Bet: 0")
        bet_label.setFont(QFont('Arial', 12))
        bet_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(bet_label, alignment=Qt.AlignCenter)
        widget.setLayout(vbox)
        widget.bet_label = bet_label  # Attach for easy access
        widget.card_labels = card_labels  # Attach for dynamic updates
        widget.cards_left_layout = left_layout
        widget.cards_last_layout = last_layout
        return widget

    def update_opponent_hand(self, bot_index, hand):
        """Display a bot's hand using 11 fixed slots.

        Shrinking/overlap rules mirror the player hand. For more
        than 5 cards, the first N-1 cards are placed in the left
        layout with negative spacing (overlap) and the final card
        is placed in the right layout without negative spacing so
        it remains fully visible.
        """
        bot_widget = self.opponent_widgets[bot_index]
        card_labels = bot_widget.card_labels
        left_layout = getattr(bot_widget, "cards_left_layout", None)
        last_layout = getattr(bot_widget, "cards_last_layout", None)
        if left_layout is None or last_layout is None:
            return

        max_slots = len(card_labels)
        visible_n = len(hand)
        base_w, base_h = 60, 90
        max_total_width = 300
        n = visible_n if visible_n > 0 else 1

        # Determine card size and whether we need overlap based
        # on the number of visible cards.
        if n <= 2:
            card_w, card_h = base_w, base_h
            use_overlap = False
        elif 3 <= n <= 5:
            scale = min(1.0, max_total_width / float(n * base_w))
            card_w = max(30, int(base_w * scale))
            card_h = max(45, int(base_h * scale))
            use_overlap = False
        else:
            # 6 or more cards: size them as if there were 5,
            # then overlap to the right.
            n_for_size = 5
            scale = min(1.0, max_total_width / float(n_for_size * base_w))
            card_w = max(30, int(base_w * scale))
            card_h = max(45, int(base_h * scale))
            use_overlap = True

        # Nothing to show
        if visible_n <= 0:
            for lbl in card_labels:
                lbl.hide()
            return

        # For 1–5 cards, keep all cards contiguous (spacing=0) by
        # using only non-negative spacing. For 6+, apply negative
        # spacing only to the overlapped group in the left layout
        # so the final card (in last_layout) stays fully visible.
        if use_overlap and visible_n > 5:
            overlap_fraction = 0.75
            spacing = -int(card_w * overlap_fraction)
            left_layout.setSpacing(spacing)
        else:
            left_layout.setSpacing(0)
        last_layout.setSpacing(0)

        for i in range(max_slots):
            lbl = card_labels[i]
            if i < visible_n:
                card = hand[i]
                lbl.setFixedSize(card_w, card_h)
                pixmap = QPixmap(f"cards_graphic/{card}.png").scaled(card_w, card_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl.setPixmap(pixmap)
                lbl.show()
                if use_overlap and visible_n > 5 and i == visible_n - 1:
                    # Last card for 6+ goes in the right layout
                    last_layout.addWidget(lbl)
                else:
                    left_layout.addWidget(lbl)
            else:
                lbl.hide()
            
    def create_dealer_widget(self):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel("Dealer")
        name_label.setFont(QFont('Arial', 16))
        hbox = QHBoxLayout()
        card_labels = []
        for _ in range(2):
            card_label = QLabel()
            card_label.setFixedSize(80, 120)
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hbox.addWidget(card_label)
            card_labels.append(card_label)
        vbox.addWidget(name_label, alignment=Qt.AlignCenter)
        vbox.addLayout(hbox)
        widget.setLayout(vbox)
        widget.card_labels = card_labels  # Attach for dynamic updates
        return widget
    
    def update_dealer_hand(self, hand):
        dealer_widget=self.dealer_widget
        # Adjust number of card labels if needed
        while len(dealer_widget.card_labels) < len(hand):
            card_label = QLabel()
            card_label.setFixedSize(80, 120)
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            dealer_widget.layout().itemAt(1).layout().addWidget(card_label)
            dealer_widget.card_labels.append(card_label)
        while len(dealer_widget.card_labels) > len(hand):
            label = dealer_widget.card_labels.pop()
            dealer_widget.layout().itemAt(1).layout().removeWidget(label)
            label.deleteLater()
        # Update card images
        for i, card in enumerate(hand):
            pixmap = QPixmap(f"cards_graphic/{card}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            dealer_widget.card_labels[i].setPixmap(pixmap)
            dealer_widget.card_labels[i].show()
    
    def set_player_name(self, player_name):
        self.player_name = player_name
        # Re-initialize wallet and UI elements as needed
        wallet_from_db = self.get_wallet_from_db(self.player_name)
        override_wallet = False
        if override_wallet or wallet_from_db is None:
            self.wallet = 1000
        else:
            self.wallet = wallet_from_db
        self.wallet_label.setText(f"Wallet: ${self.wallet}")
    
    def get_wallet_from_db(self, player_name):
        wallet = self.db_helper.retrieve_player_wallet(player_name)
        if wallet is not None:
            return wallet
        return None
    
    def update_opponents(self, num_opponents):
        # Hide all first
        for opp in self.opponent_widgets:
            opp.hide()
        for i in range(num_opponents):
            self.opponent_widgets[i].show()
    
    def set_bot_count(self, bot_count):
        self.bot_count = bot_count
        self.update_opponents(bot_count)
        
    def start_game(self):
        player_names = [self.player_name] + [f"Bot{i}" for i in range(1, self.bot_count + 1)]
        self.active_hand_index=0
        # Reset round message and flags
        self.clear_round_message()
        self.had_push_this_round = False
        self.dealer_blackjack_round = False
        self._prompted_this_round = False
        self.blackjack_game = BlackjackGame(player_names,
                                    action_callback=self.on_action_requested,
                                    phase_callback=self.on_phase,
                                    pot_update_callback=self.update_pot,
                                    bot_bet_update_callback=self.update_bot_bet,
                                    bot_fold_callback=self.on_bot_fold
                                    )
        self.blackjack_game.start_game()
    def on_initial_bet(self):
        bet_amount = self.bet_input.text()
        # Process bet_amount as needed
        self.initial_bet_button.hide()
        self.bet_input.hide()
        if hasattr(self, 'bet_label') and self.bet_label is not None:
            self.bet_label.hide()
        self.blackjack_game.initial_bet_received(int(bet_amount))
        
    def on_action_requested(self, player, hand_index, options):
        if "initial_bet" in options:
            self.bet_input.show()
            self.initial_bet_button.show()
            self.initial_bet_button.clicked.disconnect()  # Remove previous connections if any
            self.initial_bet_button.clicked.connect(lambda: self.submit_initial_bet())
            self.disable_action_buttons()
        else:
            # Handle normal actions (hit, stand, etc.)
            self.current_player = player
            self.current_hand_index = hand_index
            self.enable_action_buttons(options)
            
    def submit_initial_bet(self):
        bet_amount = int(self.bet_input.text())
        self.bet_input.hide()
        self.initial_bet_button.hide()
        if hasattr(self, 'bet_label') and self.bet_label is not None:
            self.bet_label.hide()
        self.blackjack_game.initial_bet_received(bet_amount)
    
    def enable_action_buttons(self, options):
        self.hit_button.setEnabled('hit' in options)
        self.stand_button.setEnabled('stand' in options)
        self.double_down_button.setEnabled('double_down' in options)
        self.surrender_button.setEnabled('surrender' in options)
        self.split_button.setEnabled('split' in options)
    
    def disable_action_buttons(self):
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        self.double_down_button.setEnabled(False)
        self.surrender_button.setEnabled(False)
        self.split_button.setEnabled(False)
    
    def on_action_button_clicked(self, action):
        self.blackjack_game.process_player_action(self.current_player, self.current_hand_index, action)
        
    def _get_bot_index_by_name(self, player_name):
        """Map a bot player's name (e.g. 'Bot1') to its opponent_widgets index."""
        try:
            if not hasattr(self, "blackjack_game") or not self.blackjack_game:
                return None
            bots = [p for p in self.blackjack_game.players if getattr(p, "isBot", False)]
            for idx, p in enumerate(bots):
                if p.name == player_name:
                    return idx
        except Exception:
            pass
        return None
        
    def on_phase(self, phase, data: dict):
        print("DEBUG: Blackjack phase:", phase, data)
        if phase == "initial_deal":
            players = data["players"]
            main_player = next(p for p in players if not p.isBot)
            # Show only main player's two cards
            self.set_hands([main_player.hand], 0)
            # Show only the first card for each bot
            bot_players = [p for p in players if p.isBot]
            for i, bot in enumerate(bot_players):
                # Use strings, not nested lists; show first card and hide second
                first_card = bot.hand[0] if bot.hand else "card_back"
                cards = [first_card, "card_back"] if len(bot.hand) > 1 else [first_card]
                self.update_opponent_hand(i, cards)
            # Show dealer's cards as appropriate
            dealer_hand = data["dealer"]
            self.update_dealer_hand(dealer_hand)
        elif phase == "dealer_blackjack":
            # Dealer has blackjack. Reveal dealer and all player hands; annotate outcomes.
            dealer_hand = data.get("dealerHand", [])
            self.update_dealer_hand(dealer_hand)
            players_info = data.get("players") or data.get("players_info", [])

            # Update main player's hand
            main_info = next((pi for pi in players_info if not pi.get("isBot", False)), None)
            if main_info and main_info.get("hand"):
                self.set_hands([main_info["hand"]], 0)

            # Reveal bot hands and mark push/lose
            bot_idx = 0
            for pi in players_info:
                if pi.get("isBot", False):
                    hand = pi.get("hand", [])
                    self.update_opponent_hand(bot_idx, hand)
                    # Annotate outcome on bet label
                    outcome_text = "Push" if pi.get("hasBlackjack", False) else "Lose"
                    self.opponent_widgets[bot_idx].bet_label.setText(outcome_text)
                    bot_idx += 1

            self.disable_action_buttons()
            self.dealer_blackjack_round = True
            self.append_round_message("Dealer has blackjack. Resolving outcomes...")
        elif phase == "player_blackjack":
            # Main player has blackjack and wins immediately.
            player_info = data.get("player", {})
            winnings = data.get("winnings", 0)
            hand = data.get("hand", [])
            if hand:
                self.set_hands([hand], 0)
            self.disable_action_buttons()
            self.append_round_message(f"{player_info.get('name','Player')} wins ${winnings}.")
            self.refresh_wallet_label()
        elif phase == "push_result":
            # Main player pushes vs dealer blackjack; bet returned.
            player_info = data.get("player", {})
            self.disable_action_buttons()
            self.had_push_this_round = True
            self.append_round_message(f"{player_info.get('name','Player')} pushes. Bet returned.")
            self.refresh_wallet_label()
        elif phase == "dealer_instant_win_end":
#            immediate_result = (player,winnings)
            dealerTotal=data[0]
            immediate_result=data[1]
            if immediate_result is not None:
                player, winnings = immediate_result
                message = f"Player {player.name} wins. Winnings: {winnings}"
            else:
                message = f"Dealer has blackjack with total {dealerTotal}. All players lose."
            # Suppress misleading lose message when a push occurred; otherwise show.
            if not self.had_push_this_round:
                self.append_round_message(message)
            # Mark all bots as having lost in this scenario
            try:
                for opp in self.opponent_widgets:
                    opp.bet_label.setText("Lose")
            except Exception:
                pass
            self.disable_action_buttons()
            self.refresh_wallet_label()
        elif phase == "bot_hand_update":
            # {"name": player.name, "hand": hand, "hand_index": hand_index}
            player_name = (data or {}).get("name", "Bot")
            hand = (data or {}).get("hand") or []
            bot_index = self._get_bot_index_by_name(player_name)
            if bot_index is not None and 0 <= bot_index < len(self.opponent_widgets):
                # Reveal all current bot cards (including second and any hits)
                self.update_opponent_hand(bot_index, hand)

        elif phase == "bot_bust":
            # Show all bot cards and mark the bet label as busted
            player_name = (data or {}).get("name", "Bot")
            hand = (data or {}).get("hand") or []
            bot_index = self._get_bot_index_by_name(player_name)
            if bot_index is not None and 0 <= bot_index < len(self.opponent_widgets):
                self.update_opponent_hand(bot_index, hand)
                try:
                    self.opponent_widgets[bot_index].bet_label.setText("Busted")
                except Exception:
                    pass

        elif phase == "bot_stand":
            # Final bot hand: show all cards, keep existing bet label text
            player_name = (data or {}).get("name", "Bot")
            hand = (data or {}).get("hand") or []
            bot_index = self._get_bot_index_by_name(player_name)
            if bot_index is not None and 0 <= bot_index < len(self.opponent_widgets):
                self.update_opponent_hand(bot_index, hand)
            
        # returned data: {"name":..., "hands":..., "bets":..., "hand_index": ...}
        if phase in ("player_action", "hit", "stand", "double_down", "surrender", "split", "bust"):
            # Keep hand highlights in sync with engine
            if data is not None and "hands" in data:
                hands = data["hands"] if data["hands"] else [self.blackjack_game.players[0].hand]
                # Default to engine-provided active hand index
                idx = data.get("hand_index", 0)
                # On bust, immediately advance highlight to the next hand if it exists
                if phase == "bust" and idx + 1 < len(hands):
                    idx = idx + 1
                self.active_hand_index = idx
                self.set_hands(hands, self.active_hand_index)

            if phase in ("stand", "surrender", "split", "bust"):
                self.disable_action_buttons()
            elif phase == "error":
                error_message = "An error occurred. How did you get here?"
                QMessageBox.critical(self, "Error", error_message)
            elif phase == "funds_error":
                error_message = "You don't have enough funds to make that bet."
                QMessageBox.warning(self, "Funds Error", error_message)
        elif phase == 'round_end':
            # Dealer finished playing out; show final dealer hand and net result
            dealer_total = None
            net_winnings = None
            hand_results = None
            try:
                # Support both tuple/list and dict payloads
                if isinstance(data, (list, tuple)) and len(data) >= 2:
                    dealer_total, net_winnings = data[0], data[1]
                elif isinstance(data, dict):
                    dealer_total = data.get('dealerTotal')
                    net_winnings = data.get('netWinnings')
                    hand_results = data.get('handResults')
            except Exception:
                dealer_total = None
                net_winnings = None

            # Update dealer hand to the final state
            if hasattr(self, 'blackjack_game') and self.blackjack_game:
                final_dealer_hand = self.blackjack_game.dealer.get_hand()
                self.update_dealer_hand(final_dealer_hand)
                # Reveal all bot hands consistently at round end
                try:
                    print("DEBUG: Revealing bot hands at round end")
                    bot_idx = 0
                    for node in self.blackjack_game.player_nodes:
                        p = node.player
                        if getattr(p, 'isBot', False):
                            hand_to_show = p.hand if getattr(p, 'hand', None) else []
                            self.update_opponent_hand(bot_idx, hand_to_show)
                            bot_idx += 1
                except Exception:
                    print("DEBUG: Failed to reveal bot hands at round end")
                    pass

            # Summarize outcome in the round message label (engine provides final results)
            summary = []
            if dealer_total is not None:
                summary.append(f"Dealer total: {dealer_total}")
            if net_winnings is not None:
                summary.append(f"Net winnings: ${net_winnings}")
            # Build per-hand details: rely on engine-provided results
            processed_results = hand_results if isinstance(hand_results, list) else []
            # Enumerate all results; ensure last hand is included
            #print ("DEBUG processed_results:", processed_results)
            for i, hr in enumerate(processed_results, start=1):
                print (f"DEBUG: Hand {i} result data: {hr}")
                result_text = (hr.get('result') or '').capitalize()
                bet_val = hr.get('bet', 0)
                payout_val = hr.get('winnings', 0)
                summary.append(f"Hand {i}: {result_text} | Bet ${bet_val} | Payout ${payout_val}")
            print ("DEBUG\n"+ "\n".join(summary))
            if summary:
                # Replace any prior update/debug text with the final summary
                self.show_round_message("\n".join(summary))

            # Disable actions and refresh wallet to reflect payouts
            self.disable_action_buttons()
            self.refresh_wallet_label()
            # Prompt to play again after non-immediate rounds as well, with a short delay
            if not getattr(self, '_prompted_this_round', False):
                QTimer.singleShot(1500, self.prompt_play_again)
        
        
        elif phase =="update":
            # After completing a hand via stand/surrender, move to the next split hand
            name = (data or {}).get("name", "Player")
            hands = (data or {}).get("hands") or []
            bets = (data or {}).get("bets") or []
            idx = (data or {}).get("hand_index", 0)  # next active hand index
            total_hands = len(hands) if hands else 1

            # Replace the round message (do not append for update)
            if idx < total_hands:
                current_bet = bets[idx] if (bets and idx < len(bets)) else None
                bet_text = f" | Bet: ${current_bet}" if current_bet is not None else ""
                self.show_round_message(f"{name}: Next hand ({idx+1}/{total_hands}){bet_text}.")
            else:
                self.show_round_message(f"{name}: All hands completed.")

            # Reflect the new active hand and pause inputs until next prompt
            if hands:
                self.active_hand_index = idx
                self.set_hands(hands, self.active_hand_index)
            self.disable_action_buttons()
        self.update_hand_type()

    def show_round_message(self, text):
        self.round_message_label.setText(text)
        self.round_message_label.show()
        self.position_round_message()

    def clear_round_message(self):
        self.round_message_label.hide()
        self.round_message_label.setText("")

    def append_round_message(self, text):
        existing = self.round_message_label.text() or ""
        if existing:
            combined = existing + "\n" + text
        else:
            combined = text
        self.round_message_label.setText(combined)
        self.round_message_label.show()
        self.position_round_message()

    def position_round_message(self):
        # Overlay the round message relative to the full screen content area
        try:
            content_rect = self.rect()
            margin = 10
            fm = QFontMetrics(self.round_message_label.font())
            text = self.round_message_label.text() or ""
            lines = text.split("\n") if text else [""]
            # Compute width based on the longest line of text, plus padding/border and small safety fudge
            longest = max((fm.boundingRect(line).width() for line in lines), default=0)
            padding_w = 20  # style: padding: 2px 10px -> horizontal total = 20
            border_w = 2    # style: border: 1px solid -> left+right = 2
            fudge_w = 3     # small safety to avoid off-by-1 wraps
            # Ensure a sensible minimum width to avoid excessive wrapping
            min_w = 220
            w = min(max(longest + padding_w + border_w + fudge_w, min_w), content_rect.width() - 2 * margin)
            # Compute height using a QTextDocument for accurate multi-line+wrap layout
            padding_h = 0
            doc = QTextDocument()
            doc.setDefaultFont(self.round_message_label.font())
            # Inner text width excludes horizontal padding and border
            doc.setTextWidth(max(0, w - (padding_w + border_w)))
            doc.setPlainText(text)
            doc_height = int(doc.size().height())
            # Avoid clipping: allow up to the available height minus margins
            h = min(doc_height + padding_h, content_rect.height() - 2 * margin)
            # Center horizontally in the screen
            x = (content_rect.width() - w) // 2
            # Place above the chips: convert chips position to screen coordinates
            try:
                chips_top_left = self.chips_widget.mapTo(self, QPoint(0, 0))
                y = max(margin, chips_top_left.y() - h - margin)
            except Exception:
                y = content_rect.height() - h - margin
            self.round_message_label.setGeometry(x, y, w, h)
            self.round_message_label.raise_()
        except Exception:
            pass

    def refresh_wallet_label(self):
        # Update wallet label from the current main player's wallet
        if hasattr(self, 'blackjack_game') and self.blackjack_game:
            player_nodes = self.blackjack_game.player_nodes
            main_player_node = next((node for node in player_nodes if not node.player.isBot), None)
            if main_player_node is not None:
                self.wallet = main_player_node.player.wallet
                self.wallet_label.setText(f"Wallet: ${self.wallet}")
    def update_hand_type(self):
        # Get the player's hand and table cards
        player_nodes = self.blackjack_game.player_nodes
        main_player_node = next(node for node in player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        player_hands=main_player.hands if main_player.hands else [main_player.hand]
        self.set_hands(player_hands, self.active_hand_index)
        # Use Blackjack's evaluate_hand
        print(f"DEBUG: Evaluating hand for {main_player.name}. Hands: {main_player.hands}, Bets: {main_player.bets}, Active hand index: {self.active_hand_index}")
        if not main_player.hands:
            hand = main_player.hand
        else:
            if self.active_hand_index is not None:
                hand = main_player.hands[self.active_hand_index]
            else:
                hand = main_player.hand
        total = self.blackjack_game.evaluator.evaluate_hand(hand)
        print(f"Hand total: {total}. Hand: {hand}")
        self.hand_total_label.setText(f"Current Hand: {', '.join(hand)}, {total}")
    
    
    def update_pot(self, amount):
        self.pot_label.setText(f"Pot: {amount}")
    
    def update_bot_bet(self, bot_index, amount):
        # bot_index: 0 for Bot1, 1 for Bot2, etc.
        bot_widget = self.opponent_widgets[bot_index]
        bot_widget.bet_label.setText("Bet: " + str(amount))

    def on_bot_fold(self, bot_index ,hand):
        bot_widget = self.opponent_widgets[bot_index]
        bot_widget.bet_label.setText("Folded")
        card_labels = bot_widget.findChildren(QLabel)[1:3]  # Adjust if needed
        card_labels[0].setPixmap(QPixmap(f"cards_graphic/{hand[0]}.png").scaled(60, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        card_labels[1].setPixmap(QPixmap(f"cards_graphic/{hand[1]}.png").scaled(60, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def prompt_play_again(self):
        self._prompted_this_round = True
        msg = QMessageBox(self)
        msg.setWindowTitle("Play Again?")
        msg.setText("Would you like to play another round?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        result = msg.exec_()
        if result == QMessageBox.Yes:
            # Attempt minimal UI reset for opponents
            try:
                for opp in getattr(self, "opponent_widgets", []):
                    if hasattr(opp, "bet_label"):
                        opp.bet_label.setText("Bet: None")
                    for lbl in getattr(opp, "card_labels", []):
                        lbl.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(60, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception:
                pass
            self.start_game()
        else:
            # Remain on the Blackjack screen; do nothing further
            pass

class PokerGameScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window=parent
        layout = QVBoxLayout()
        
        self.bot_count=5
        
        # --- Inner poker table (green) ---
        self.bg_frame = QFrame(self)
        self.bg_frame.setStyleSheet("background-color: #357a38; border-radius: 14px;")
        self.bg_frame.setGeometry(self.rect())
        self.bg_frame.lower()
        # Background overlay should not drive layout sizing
        self.bg_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.bg_frame.show()
        
        # --------------------------
        # --- Horizontal top bar ---
        self.wallet_label = QLabel("Wallet: $1000")  # Example starting value
        self.wallet_label.setFont(QFont('Arial', 14))
        self.wallet_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.wallet_label)

        layout.addLayout(top_bar_layout)
        
        # --- Bet label and input above cards ---
        bet_label = QLabel("Enter your bet:", self)
        bet_label.setFont(QFont('Arial', 16))

        self.bet_input = QLineEdit(self)
        self.bet_input.setPlaceholderText("Amount")
        self.bet_input.setFixedWidth(100)

        bet_input_layout = QHBoxLayout()
        bet_input_layout.addWidget(bet_label)
        bet_input_layout.addWidget(self.bet_input)
        
        self.bet_error_label = QLabel("")
        self.bet_error_label.setStyleSheet("color: red;")
        
        bet_input_vlayout = QVBoxLayout()
        bet_input_vlayout.addLayout(bet_input_layout)
        self.bet_error_label = QLabel("")
        self.bet_error_label.setStyleSheet("color: red;")
        bet_input_vlayout.addWidget(self.bet_error_label, alignment=Qt.AlignCenter)
        bet_input_widget = QWidget()
        bet_input_widget.setLayout(bet_input_vlayout)
        
        
        # --- Player cards ---
        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignCenter)
        cards_layout.setSpacing(0)
        self.card1_label = QLabel(self)
        self.card2_label = QLabel(self)
        self.card1_label.setFixedSize(80, 120)
        self.card2_label.setFixedSize(80, 120)
        self.set_cards("AS", "10H")
        cards_layout.addWidget(self.card1_label)
        cards_layout.addWidget(self.card2_label)
        cards_widget = QWidget()
        cards_widget.setLayout(cards_layout)

        # --- Betting buttons stacked vertically ---
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        self.raise_button = QPushButton("Raise Bet", self)
        self.raise_button.setFixedWidth(90)
        self.raise_button.clicked.connect(self.on_bet_submitted)
        self.call_button = QPushButton("Call Bet", self)
        self.call_button.setFixedWidth(90)
        self.call_button.clicked.connect(self.call_bet)
        self.check_button = QPushButton("Check", self)
        self.check_button.setFixedWidth(90)
        self.check_button.clicked.connect(self.check)
        self.fold_button = QPushButton("Fold", self)
        self.fold_button.setFixedWidth(90)
        self.fold_button.clicked.connect(self.fold)
        buttons_layout.addWidget(self.raise_button)
        buttons_layout.addWidget(self.call_button)
        buttons_layout.addWidget(self.check_button)
        buttons_layout.addWidget(self.fold_button)
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        
        # ---------------------
        # # Create placeholders for up to 5 opponents, start hidden
        self.opponent_widgets = []
        for i in range(5):
            opp = self.create_opponent_widget(f"Bot {i+1}")
            self.opponent_widgets.append(opp)
        
        # --- Table area with grid layout ---
        table_area = QGridLayout()
        table_area.setColumnStretch(0, 1)
        table_area.setColumnStretch(1, 0)
        table_area.setColumnStretch(2, 1)
        table_area.setRowStretch(0, 1)
        table_area.setRowStretch(1, 0)
        table_area.setRowStretch(2, 1)

        # Top opponent (centered)
        table_area.addWidget(self.opponent_widgets[0], 0, 1, alignment=Qt.AlignCenter)
        # Left opponent
        table_area.addWidget(self.opponent_widgets[1], 1, 0, alignment=Qt.AlignLeft)
        # Right opponent
        table_area.addWidget(self.opponent_widgets[2], 1, 2, alignment=Qt.AlignRight)
        # Bottom left opponent
        table_area.addWidget(self.opponent_widgets[3], 2, 0, alignment=Qt.AlignLeft)
        # Bottom right opponent
        table_area.addWidget(self.opponent_widgets[4], 2, 2, alignment=Qt.AlignRight)
        # Table cards (center)
        self.table_cards_widget = QWidget()
        table_cards_layout = QHBoxLayout()
        table_cards_layout.setContentsMargins(0, 0, 0, 0)
        table_cards_layout.setSpacing(4)
        self.table_card_labels = []
        for _ in range(5):
            card_label = QLabel()
            # Reserve space for each community card from the start so
            # the layout (and thus the window) always accounts for all 5.
            card_label.setFixedSize(80, 120)
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.table_card_labels.append(card_label)
            table_cards_layout.addWidget(card_label)
        self.table_cards_widget.setLayout(table_cards_layout)
        
        layout.addLayout(table_area)
        # --- Center column: stack table cards, pot label, chips widget ---
        center_col_layout = QVBoxLayout()
        center_col_layout.setAlignment(Qt.AlignCenter)
        self.pot_label = QLabel("Pot: 0")
        self.pot_label.setFont(QFont('Arial',14))
        self.pot_label.setAlignment(Qt.AlignCenter)
        self.chips_widget = QLabel("CHIPS PLACEHOLDER")
        self.chips_widget.setMinimumSize(200, 40)
        self.chips_widget.setStyleSheet("background: #bbb; border: 2px solid #888; border-radius: 8px;")
        
        # Center column layout
        center_col_layout.addSpacing(32)
        center_col_layout.addWidget(self.table_cards_widget, alignment=Qt.AlignCenter)
        center_col_layout.addSpacing(16)
        center_col_layout.addWidget(self.pot_label, alignment=Qt.AlignCenter)
        center_col_layout.addSpacing(16)
        center_col_layout.addWidget(self.chips_widget, alignment=Qt.AlignCenter)

        center_col_widget = QWidget()
        center_col_widget.setLayout(center_col_layout)
        table_area.addWidget(center_col_widget, 1, 1, alignment=Qt.AlignCenter)
        
        # --- Combine cards and buttons horizontally ---
        cards_and_buttons_layout = QHBoxLayout()
        cards_and_buttons_layout.addWidget(cards_widget)
        cards_and_buttons_layout.addSpacing(20)
        cards_and_buttons_layout.addWidget(buttons_widget)
        cards_and_buttons_widget = QWidget()
        cards_and_buttons_widget.setLayout(cards_and_buttons_layout)

        
        self.hand_type_label = QLabel("Hand: ")
        self.hand_type_label.setFont(QFont('Arial', 14))
        #self.hand_type_label.setStyleSheet("color: #222;")
        layout.addWidget(self.hand_type_label, alignment=Qt.AlignCenter)
        
        
        # --- Add to main layout ---
        layout.addWidget(bet_input_widget, alignment=Qt.AlignCenter)
        layout.addWidget(cards_and_buttons_widget, alignment=Qt.AlignCenter)

        
        # Prevent squishing: enforce minimum size equal to layout's size hint
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.setLayout(layout)
        try:
            self.setMinimumSize(self.sizeHint())
        except Exception:
            pass
        
        self.db_helper=DBHelper()
        
    def start_game(self):
        player_names = [self.player_name] + [f"Bot{i}" for i in range(1, self.bot_count + 1)]
        self.poker_game = PokerGame(player_names,
                                    action_callback=self.on_bet_requested,
                                    phase_callback=self.on_phase,
                                    pot_update_callback=self.update_pot,
                                    bot_bet_update_callback=self.update_bot_bet,
                                    bot_fold_callback=self.on_bot_fold
                                    )
        self.poker_game.start_game()
    
    def resizeEvent(self, event):
        # Ensure the background frame always fills the PokerGameScreen
        self.bg_frame.setGeometry(self.rect())
        super().resizeEvent(event)
        
    def set_player_name(self, player_name):
        self.player_name = player_name
        # Re-initialize wallet and UI elements as needed
        wallet_from_db = self.get_wallet_from_db(self.player_name)
        override_wallet = False
        if override_wallet or wallet_from_db is None:
            self.wallet = 1000
        else:
            self.wallet = wallet_from_db
        self.wallet_label.setText(f"Wallet: ${self.wallet}")
    
    def set_bot_count(self, bot_count):
        self.bot_count = bot_count
        self.update_opponents(bot_count)
    
        
    def set_cards(self, card1, card2):
        # Assumes images are named like 'AS.png', '10H.png' in a 'cards' folder
        pixmap1 = QPixmap(f"cards_graphic/{card1}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap2 = QPixmap(f"cards_graphic/{card2}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.card1_label.setPixmap(pixmap1)
        self.card2_label.setPixmap(pixmap2)
    
    def update_hand_type(self):
        # Get the player's hand and table cards
        player = self.poker_game.players[0]
        hand = player.hand
        table = self.poker_game.dealt
        # Use Poker_for_GUI's evaluate_hand
        print (hand, table)
        rank, cards, hand_type = self.poker_game.evaluator.evaluate_hand(hand, table)
        self.hand_type_label.setText(f"Hand: {hand_type}")
    
    
    def create_opponent_widget(self, name):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 16))
        card1 = QLabel()
        card2 = QLabel()
        card1.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        card2.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        hbox = QHBoxLayout()
        hbox.addWidget(card1)
        hbox.addWidget(card2)
        vbox.addWidget(name_label, alignment=Qt.AlignCenter)
        vbox.addLayout(hbox)
        bet_label = QLabel("Bet: 0")
        bet_label.setFont(QFont('Arial', 12))
        bet_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(bet_label, alignment=Qt.AlignCenter)
        widget.setLayout(vbox)
        widget.bet_label = bet_label  # Attach for easy access
        return widget

    def update_pot(self, amount):
        self.pot_label.setText(f"Pot: {amount}")

    def update_bot_bet(self, bot_index, amount):
        # bot_index: 0 for Bot1, 1 for Bot2, etc.
        bot_widget = self.opponent_widgets[bot_index]
        bot_widget.bet_label.setText("Bet: " + str(amount))

    def on_bot_fold(self, bot_index ,hand):
        bot_widget = self.opponent_widgets[bot_index]
        bot_widget.bet_label.setText("Folded")
        card_labels = bot_widget.findChildren(QLabel)[1:3]  # Adjust if needed
        card_labels[0].setPixmap(QPixmap(f"cards_graphic/{hand[0]}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        card_labels[1].setPixmap(QPixmap(f"cards_graphic/{hand[1]}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    

    def update_opponents(self, num_opponents):
        # Hide all first
        for opp in self.opponent_widgets:
            opp.hide()
        for i in range(num_opponents):
            self.opponent_widgets[i].show()
    
    def on_phase(self, phase, data=None):
        if phase == 'initial_hands':
            player_hand = data[0].hand  # Assuming first player is human
            self.set_cards(player_hand[0], player_hand[1])
            # Clear table cards
            for card_label in self.table_card_labels:
                card_label.clear()
        elif phase =='flop':
            # Update table cards display
            for i in range(3):
                self.table_card_labels[i].setPixmap(QPixmap(f"cards_graphic/{data[i]}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif phase == 'turn':
            card = data[-1]  # The new turn card
            self.table_card_labels[3].setPixmap(QPixmap(f"cards_graphic/{card}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif phase == 'river':
            card = data[-1]  # The new river card
            self.table_card_labels[4].setPixmap(QPixmap(f"cards_graphic/{card}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif phase == 'showdown':
            if data is None:
                print("Showdown phase called with data=None!")
            if data is not None:
                bot_hands = []
                for player in data[1:]:  # Exclude human player
                    if player is not None and player.hand is not None:
                        bot_hands.append(player.hand)
                    else:
                        # Fallback: show card backs if hand is missing
                        bot_hands.append(['card_back', 'card_back'])
                self.reveal_all_bot_hands(bot_hands)
            #self.reveal_all_bot_hands([player.hand for player in data[1:]])  # Exclude human player
        elif phase == 'winner':
            winner_name, winning_hand, pot = data
            self.show_game_result_prompt(winner_name, pot)
        # Update hand type after each phase
        self.update_hand_type()
    
    
    def show_game_result_prompt(self, winner_name, winnings):
        msg = QMessageBox(self)
        msg.setWindowTitle("Game Over")
        msg.setText(f"{winner_name} wins ${winnings}!\n\nPlay again?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        result = msg.exec_()
        if result == QMessageBox.Yes:
            self.reset_bot_cards()
            self.start_game()
        else:
            pass
            
    def reset_bot_cards(self):
        for bot_widget in self.opponent_widgets:
            # Find the card labels (assuming they are the 2nd and 3rd QLabel children)
            card_labels = bot_widget.findChildren(QLabel)[1:3]
            for card_label in card_labels:
                card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            bot_widget.bet_label.setText("Bet: 0")
    
    def reveal_all_bot_hands(self, bot_hands):
        """
        bot_hands: list of lists, e.g. [['AS', '10H'], ['2D', '3C'], ...]
        """
        for i, hand in enumerate(bot_hands):
            if i < len(self.opponent_widgets):
                bot_widget = self.opponent_widgets[i]
                # Find the card labels (assuming they are the 2nd and 3rd QLabel children)
                card_labels = bot_widget.findChildren(QLabel)[1:3]
                card_labels[0].setPixmap(QPixmap(f"cards_graphic/{hand[0]}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                card_labels[1].setPixmap(QPixmap(f"cards_graphic/{hand[1]}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def update_player_cards(self, hand):
        # hand is a list like ['AS', '10H']
        self.card1_label.setPixmap(QPixmap(f"cards/{hand[0]}.png"))
        self.card2_label.setPixmap(QPixmap(f"cards/{hand[1]}.png"))
    
    
    def disable_betting_buttons(self):
        self.bet_input.setEnabled(False)
        self.raise_button.setEnabled(False)
        self.call_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.fold_button.setEnabled(False)
        
    def activate_betting_buttons(self):
        self.bet_input.setEnabled(True)
        self.raise_button.setEnabled(True)
        self.call_button.setEnabled(True)
        self.check_button.setEnabled(True)
        self.fold_button.setEnabled(True)
        
    def call_bet(self):
        player=self.poker_game.players[0]
        minimum_bet = self.poker_game._betting_current_bet - player.current_bet
        if minimum_bet>player.wallet:
            minimum_bet=player.wallet
        self.on_bet_submitted(minimum_bet)
        
    def check(self):
        player = self.poker_game.players[0]
        minimum_bet = self.poker_game._betting_current_bet - player.current_bet
        if minimum_bet == 0:
            self.on_bet_submitted(0)
        else:
            self.bet_error_label.setText("Cannot check, you must call or raise.")
    
    def fold(self):
        player = self.poker_game.players[0]
        player.isFolded = True
        self.disable_betting_buttons()
        self.poker_game.resume_betting_round()
    
    def on_bet_requested(self, minimum_bet):
        # Show input box, wait for user to submit
        self.bet_input.setText(str(minimum_bet))
        self.activate_betting_buttons()
    
        
    def on_bet_submitted(self, minimum_bet):
        try:
            amount = int(self.bet_input.text())
        except ValueError:
            self.bet_error_label.setText("Please enter a valid number.")
            return

        if amount < minimum_bet:
            self.bet_error_label.setText(f"Bet must be at least {minimum_bet}.")
            return
        player = self.poker_game.players[0]
        if amount > player.wallet:
            self.bet_error_label.setText("You do not have enough funds.")
            return
        if amount < 0:
            self.bet_error_label.setText("Bet must be positive.")
            return
        
        # Valid input
        self.bet_error_label.setText("")
        player.add_to_bet(amount)
        self.disable_betting_buttons()
        self.wallet = player.wallet  # Update internal wallet value
        self.update_wallet(self.wallet)

        self.poker_game.resume_betting_round()
    
    def update_wallet(self, amount):
        self.wallet_label.setText(f"Wallet: ${amount}")
    
    def get_wallet_from_db(self, player_name):
        wallet = self.db_helper.retrieve_player_wallet(player_name)
        if wallet is not None:
            return wallet
        return None

    def _get_bot_index_by_name(self, player_name):
        """Map a bot player's name (e.g. 'Bot1') to its opponent_widgets index."""
        try:
            if not hasattr(self, "blackjack_game") or not self.blackjack_game:
                return None
            bots = [p for p in self.blackjack_game.players if getattr(p, "isBot", False)]
            for idx, p in enumerate(bots):
                if p.name == player_name:
                    return idx
        except Exception:
            pass
        return None
        
    
class WelcomeScreen(QWidget):
    def __init__(self, poker_callback, blackjack_callback, five_card_poker_callback):
        super().__init__()
        self.setWindowTitle('Poker Game')
        
        self.resize(600,200)
        
        layout = QVBoxLayout()

        titleLabel = QLabel('Welcome to Card Games!', self)
        titleLabel.setFont(QFont('Times New Roman', 28))
        
        user_layout = QVBoxLayout()
        user_widget = QWidget()
        user_widget.setLayout(user_layout)
        user_widget.setMaximumWidth(260)
        user_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        user_label = QLabel("Player Name:", self)
        user_label.setFont(QFont('Arial', 16))
        user_layout.addWidget(user_label)
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter your name")
        user_layout.addWidget(self.name_input)
        
        startPokerButton = QPushButton('Start Poker Game', self)
        startPokerButton.clicked.connect(self.on_start_poker_game)
        
        startBlackjackButton = QPushButton('Start Blackjack Game', self)
        startBlackjackButton.clicked.connect(self.on_start_blackjack_game)
        startFiveCardButton = QPushButton('Start Five Card Poker Game', self)
        startFiveCardButton.clicked.connect(self.on_start_fivecard_game)
        self.poker_callback = poker_callback
        self.blackjack_callback = blackjack_callback
        self.five_card_poker_callback = five_card_poker_callback
        
        games_widget= QWidget()
        games_layout = QHBoxLayout()
        games_layout.addWidget(startPokerButton)
        games_layout.addWidget(startBlackjackButton)
        games_layout.addWidget(startFiveCardButton)
        games_widget.setLayout(games_layout)
        
        layout.addWidget(titleLabel, alignment=Qt.AlignCenter)
        layout.addWidget(user_widget, alignment=Qt.AlignCenter)
        layout.addWidget(games_widget, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        
    def on_start_poker_game(self):
        player_name = self.name_input.text() or "You"

        bot_count, ok = QInputDialog.getInt(self, "Number of Opponents", 
                                            "Enter number of opponents (1-5):", 2, 1, 5)
        if ok:
            self.poker_callback(player_name, bot_count)
    def on_start_blackjack_game(self):
        player_name = self.name_input.text() or "You"
        bot_count, ok = QInputDialog.getInt(self, "Number of Opponents", 
                                            "Enter number of opponents (1-5):", 2, 1, 5)
        if ok:
            self.blackjack_callback(player_name, bot_count)
            
    def on_start_fivecard_game(self):
        player_name= self.name_input.text() or "You"
        bot_count, ok = QInputDialog.getInt(self, "Number of Opponents", 
                                            "Enter number of opponents (1-3):", 2, 1, 3)
        if ok:
            self.five_card_poker_callback(player_name, bot_count)
            
        
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()