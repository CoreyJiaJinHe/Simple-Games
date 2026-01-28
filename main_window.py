from PyQt5.QtWidgets import QApplication, QInputDialog, QFrame,QSizePolicy, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget, QLineEdit, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QPixmap, QKeySequence
from PyQt5.QtWidgets import QShortcut

from game import Poker_for_GUI as PokerGame
from game import Database_Helper as DBHelper

class MainWindow(QWidget):
    def __init__(self,):
        super().__init__()
        self.setWindowTitle('Poker Game')
        self.resize(600, 300)

        # Poker table outer background frames
        self.outer_frame = QFrame(self)
        self.outer_frame.setStyleSheet("background: transparent; border: 8px solid red; border-radius: 30px;")
        self.outer_frame.setGeometry(self.rect())
        self.outer_frame.lower()
        self.outer_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet("background: transparent; border: 8px solid black; border-radius: 22px;")
        self.middle_frame.setGeometry(self.rect().adjusted(8, 8, 0, 0))
        self.middle_frame.lower()
        self.middle_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.outer_frame.hide()
        self.middle_frame.hide()

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        
        self.stacked_widget = QStackedWidget(self)
        self.welcome_screen = WelcomeScreen(self.show_game_screen)
        self.game_screen = GameScreen()

        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.game_screen)
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def show_game_screen(self, player_name, bot_count):
        print(f"Starting game for {player_name} vs {bot_count} bots")
        self.game_screen.set_player_name(player_name)
        self.game_screen.set_bot_count(bot_count)
        self.stacked_widget.setCurrentWidget(self.game_screen)
        self.game_screen.start_game()
        # Outermost border (red)
        self.outer_frame.show()
        
        # Middle border (black)
        self.middle_frame.show()
        
    def resizeEvent(self, event):
        # Ensure the background frame always fills the GameScreen
        self.outer_frame.setGeometry(self.rect())
        self.middle_frame.setGeometry(self.rect().adjusted(8, 8, -8, -8))
        super().resizeEvent(event)
        
class GameScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.bot_count=5
        
        # --- Inner poker table (green) ---
        self.bg_frame = QFrame(self)
        self.bg_frame.setStyleSheet("background-color: #357a38; border-radius: 14px;")
        self.bg_frame.setGeometry(self.rect())
        self.bg_frame.lower()

        self.bg_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        bet_input_widget = QWidget()
        bet_input_widget.setLayout(bet_input_layout)

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

        # --- Add to main layout ---
        layout.addWidget(bet_input_widget, alignment=Qt.AlignCenter)
        layout.addWidget(cards_and_buttons_widget, alignment=Qt.AlignCenter)

        
        self.bet_error_label = QLabel("")
        self.bet_error_label.setStyleSheet("color: red;")

        layout.addLayout(cards_layout)
        self.setLayout(layout)
        
        self.db_helper=DBHelper()
        
    def start_game(self):
        player_names = [self.player_name] + [f"Bot{i}" for i in range(1, self.bot_count + 1)]
        self.poker_game = PokerGame(player_names,
                                    bet_callback=self.on_bet_requested,
                                    phase_callback=self.on_phase,
                                    pot_update_callback=self.update_pot,
                                    bot_bet_update_callback=self.update_bot_bet,
                                    bot_fold_callback=self.on_bot_fold
                                    )
        self.poker_game.start_game()
    
    def resizeEvent(self, event):
        # Ensure the background frame always fills the GameScreen
        self.bg_frame.setGeometry(self.rect())
        super().resizeEvent(event)
    # def resizeEvent(self, event):
    #     new_width = max(0, self.width() - 200)
    #     self.middle_row_widget.setMaximumWidth(new_width)
    #     #self.middle_row_widget.setMinimumWidth(0)
    #     super().resizeEvent(event)
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
    def __init__(self, switch_callback):
        super().__init__()
        self.setWindowTitle('Poker Game')
        
        self.resize(600,300)
        
        layout = QVBoxLayout()

        titleLabel = QLabel('Welcome to Poker!', self)
        titleLabel.setFont(QFont('Times New Roman', 64))
        
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter your name")
        
        startButton = QPushButton('Start Game', self)
        self.switch_callback = switch_callback  # <-- Add this line
        startButton.clicked.connect(self.on_start_game)

        layout.addWidget(titleLabel, alignment=Qt.AlignCenter)
        layout.addWidget(self.name_input, alignment=Qt.AlignCenter)
        layout.addWidget(startButton, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        
    def on_start_game(self):
        player_name = self.name_input.text() or "You"

        bot_count, ok = QInputDialog.getInt(self, "Number of Opponents", 
                                            "Enter number of opponents (1-5):", 2, 1, 5)
        if ok:
            self.switch_callback(player_name, bot_count)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()