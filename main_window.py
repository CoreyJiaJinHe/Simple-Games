from PyQt5.QtWidgets import QApplication,QMessageBox, QInputDialog, QFrame,QSizePolicy, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget, QLineEdit, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QPixmap, QKeySequence, QGuiApplication
from PyQt5.QtWidgets import QShortcut

from game import Poker_for_GUI as PokerGame
from blackjack import BlackJack as BlackjackGame
from game import Database_Helper as DBHelper

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
            blackjack_callback=self.show_blackjack_game_screen
        )
        self.poker_game_screen = PokerGameScreen(parent=self)
        self.blackjack_game_screen = BlackjackGameScreen(parent=self)

        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.poker_game_screen)
        self.stacked_widget.addWidget(self.blackjack_game_screen)
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def show_welcome_screen(self):
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        # Hide outer frames
        self.outer_frame.hide()
        self.middle_frame.hide()
        
    def show_blackjack_game_screen(self, player_name="You", bot_count=2):
        print(f"Starting Blackjack game for {player_name} with {bot_count} bots")
        # You can prompt for player name and bot count here if needed
        self.stacked_widget.setCurrentWidget(self.blackjack_game_screen)
        self.outer_frame.show()
        self.middle_frame.show()
        self.blackjack_game_screen.set_bot_count(bot_count)
        self.blackjack_game_screen.set_player_name(player_name)
        self.blackjack_game_screen.start_game()
        # Fit window to content after screen switch
        self.adjustSize()
        
        
    def show_poker_game_screen(self, player_name="You", bot_count=2):
        print(f"Starting Poker game for {player_name} vs {bot_count} bots")
        self.poker_game_screen.set_player_name(player_name)
        self.poker_game_screen.set_bot_count(bot_count)
        self.stacked_widget.setCurrentWidget(self.poker_game_screen)
        self.poker_game_screen.start_game()
        # Outermost border (red)
        self.outer_frame.show()
        # Middle border (black)
        self.middle_frame.show()
        # Fit window to content after screen switch
        self.adjustSize()
        
        
    def resizeEvent(self, event):
        # Ensure the background frames fill the window
        self.outer_frame.setGeometry(self.rect())
        self.middle_frame.setGeometry(self.rect().adjusted(8, 8, -8, -8))
        super().resizeEvent(event)


    

class BlackjackGameScreen(QWidget):
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
        self.hands_layout = QHBoxLayout()
        self.hand_card_labels = []  # List of lists: one list of QLabel per hand

        # For debugging: set initial hands
        self.set_hands([["AS", "10H"], ["8D", "3C", "7S"], ["4H", "5D"]])  # Example: three hands

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
        
        # ---------------------
        # # Create placeholders for up to 5 opponents
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
        # # Create placeholders for up to 5 opponents
        self.dealer_widget = self.create_dealer_widget()
        table_cards_layout.addWidget(self.dealer_widget)
        self.table_cards_widget.setLayout(table_cards_layout)
        
        layout.addLayout(table_area)
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

        center_col_widget = QWidget()
        center_col_widget.setLayout(center_col_layout)
        table_area.addWidget(center_col_widget, 1, 1, alignment=Qt.AlignCenter)
        
        # --- Combine cards and buttons horizontally ---
        # cards_and_buttons_layout = QHBoxLayout()
        # cards_and_buttons_layout.addWidget(cards_widget)
        # cards_and_buttons_layout.addSpacing(20)
        # cards_and_buttons_layout.addWidget(buttons_widget)
        # cards_and_buttons_widget = QWidget()
        # cards_and_buttons_widget.setLayout(cards_and_buttons_layout)
        cards_and_buttons_layout = QHBoxLayout()
        hands_widget = QWidget()
        hands_widget.setLayout(self.hands_layout)
        cards_and_buttons_layout.addWidget(hands_widget)
        cards_and_buttons_layout.addSpacing(20)
        cards_and_buttons_layout.addWidget(buttons_widget)
        cards_and_buttons_widget = QWidget()
        cards_and_buttons_widget.setLayout(cards_and_buttons_layout)
        
        
        
        self.pot_label = QLabel("Pot: 0")
        self.pot_label.setFont(QFont('Arial',14))
        self.pot_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pot_label, alignment=Qt.AlignCenter)
        
        # --- Add to main layout ---
        layout.addWidget(bet_input_widget, alignment=Qt.AlignCenter)
        self.hand_total_label = QLabel("Hand: ")
        self.hand_total_label.setFont(QFont('Arial', 14))
        #self.hand_total_label.setStyleSheet("color: #222;")
        layout.addWidget(self.hand_total_label, alignment=Qt.AlignCenter)
        layout.addWidget(cards_and_buttons_widget, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        
        self.db_helper=DBHelper()
    def resizeEvent(self, event):
        # Ensure the background frame always fills the PokerGameScreen
        self.bg_frame.setGeometry(self.rect())
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

        for idx, hand in enumerate(hands):
            hand_layout = QHBoxLayout()
            hand_labels = []
            for card in hand:
                card_label = QLabel(self)
                card_label.setFixedSize(80, 120)
                pixmap = QPixmap(f"cards_graphic/{card}.png").scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
            self.hands_layout.addWidget(hand_widget)

    def create_opponent_widget(self, name, num_cards=2):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 16))
        hbox = QHBoxLayout()
        card_labels = []
        for _ in range(num_cards):
            card_label = QLabel()
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(60, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hbox.addWidget(card_label)
            card_labels.append(card_label)
        vbox.addWidget(name_label, alignment=Qt.AlignCenter)
        vbox.addLayout(hbox)
        bet_label = QLabel("Bet: 0")
        bet_label.setFont(QFont('Arial', 12))
        bet_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(bet_label, alignment=Qt.AlignCenter)
        widget.setLayout(vbox)
        widget.bet_label = bet_label  # Attach for easy access
        widget.card_labels = card_labels  # Attach for dynamic updates
        return widget
    def update_opponent_hand(self, bot_index, hand):
        bot_widget = self.opponent_widgets[bot_index]
        # Adjust number of card labels if needed
        while len(bot_widget.card_labels) < len(hand):
            card_label = QLabel()
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(60, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            bot_widget.layout().itemAt(1).layout().addWidget(card_label)
            bot_widget.card_labels.append(card_label)
        while len(bot_widget.card_labels) > len(hand):
            label = bot_widget.card_labels.pop()
            bot_widget.layout().itemAt(1).layout().removeWidget(label)
            label.deleteLater()
        # Update card images
        for i, card in enumerate(hand):
            pixmap = QPixmap(f"cards_graphic/{card}.png").scaled(60, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            bot_widget.card_labels[i].setPixmap(pixmap)
            bot_widget.card_labels[i].show()
            
    def create_dealer_widget(self):
        widget = QWidget()
        vbox = QVBoxLayout()
        name_label = QLabel("Dealer")
        name_label.setFont(QFont('Arial', 16))
        hbox = QHBoxLayout()
        card_labels = []
        for _ in range(2):
            card_label = QLabel()
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
                first_card = [bot.hand[0]] if bot.hand else ["card_back"]
                cards=[first_card, "card_back"] if len(bot.hand)>1 else first_card
                self.update_opponent_hand(i, cards)
            # Show dealer's cards as appropriate
            dealer_hand = data["dealer"]
            self.update_dealer_hand(dealer_hand)
        elif phase == "dealer_instant_win_end":
#            immediate_result = (player,winnings)
            dealerTotal=data[0]
            immediate_result=data[1]
            if immediate_result is not None:
                player, winnings = immediate_result
                message = f"Player {player.name} wins. Winnings: {winnings}"
            else:
                message = f"Dealer has blackjack with total {dealerTotal}. All players lose."
        
        # returned data: {"name":..., "hands":..., "bets":..., "hand_index": ...}
        if phase in ("player_action", "hit", "stand", "double_down", "surrender", "split", "bust", "update"):
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
        elif phase == 'showdown':
            pass
        #     if data is None:
        #         print("Showdown phase called with data=None!")
        #     if data is not None:
        #         bot_hands = []
        #         for player in data[1:]:  # Exclude human player
        #             if player is not None and player.hand is not None:
        #                 bot_hands.append(player.hand)
        #             else:
        #                 # Fallback: show card backs if hand is missing
        #                 bot_hands.append(['card_back', 'card_back'])
        #         self.reveal_all_bot_hands(bot_hands)
        #     #self.reveal_all_bot_hands([player.hand for player in data[1:]])  # Exclude human player
        # elif phase == 'winner':
        #     winner_name, winning_hand, pot = data
        #     self.show_game_result_prompt(winner_name, pot)
        # # Update hand type after each phase
        
        elif phase =="update":
            pass
            # player_hands = data["hands"]  # List of lists, e.g. [["AS", "10H"], ["8D", "3C"]]
            # self.active_hand_index = data.get("hand_index", 0)
        self.update_hand_type()
    
    def update_hand_type(self):
        # Get the player's hand and table cards
        player_nodes = self.blackjack_game.player_nodes
        main_player_node = next(node for node in player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        player_hands=main_player.hands if main_player.hands else [main_player.hand]
        self.set_hands(player_hands, self.active_hand_index)
        # Use Blackjack's evaluate_hand
        print(f"Evaluating hand for {main_player.name}. Hands: {main_player.hands}, Bets: {main_player.bets}, Active hand index: {self.active_hand_index}")
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
        # bet_input_widget = QWidget()
        # bet_input_widget.setLayout(bet_input_layout)

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
            card_label.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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

        
        self.setLayout(layout)
        
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
                self.table_card_labels[i].setPixmap(QPixmap(f"cards_graphic/{data[i]}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif phase == 'turn':
            card = data[-1]  # The new turn card
            self.table_card_labels[3].setPixmap(QPixmap(f"cards_graphic/{card}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif phase == 'river':
            card = data[-1]  # The new river card
            self.table_card_labels[4].setPixmap(QPixmap(f"cards_graphic/{card}.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
            self.reset_bot_cards()
            self.close()  # Or self.close() if PokerGameScreen is the main window
            self.main_window.show_welcome_screen()
            
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
        
    
class WelcomeScreen(QWidget):
    def __init__(self, poker_callback, blackjack_callback):
        super().__init__()
        self.setWindowTitle('Poker Game')
        
        self.resize(600,300)
        
        layout = QVBoxLayout()

        titleLabel = QLabel('Welcome to Poker!', self)
        titleLabel.setFont(QFont('Times New Roman', 64))
        
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter your name")
        
        startPokerButton = QPushButton('Start Poker Game', self)
        startPokerButton.clicked.connect(self.on_start_poker_game)
        
        startBlackjackButton = QPushButton('Start Blackjack Game', self)
        startBlackjackButton.clicked.connect(self.on_start_blackjack_game)
        self.poker_callback = poker_callback
        self.blackjack_callback = blackjack_callback
        

        layout.addWidget(titleLabel, alignment=Qt.AlignCenter)
        layout.addWidget(self.name_input, alignment=Qt.AlignCenter)
        layout.addWidget(startPokerButton, alignment=Qt.AlignCenter)
        layout.addWidget(startBlackjackButton, alignment=Qt.AlignCenter)
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
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()