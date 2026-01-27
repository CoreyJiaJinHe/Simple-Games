from PyQt5.QtWidgets import QApplication, QInputDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget, QLineEdit, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QPixmap, QKeySequence
from PyQt5.QtWidgets import QShortcut

from game import game_start

class MainWindow(QWidget):
    def __init__(self,):
        super().__init__()
        self.setWindowTitle('Poker Game')
        self.resize(600, 300)

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

class GameScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.bot_count=5
        
        
        self.wallet_label = QLabel("Wallet: $1000")  # Example starting value
        self.wallet_label.setFont(QFont('Arial', 14))
        self.wallet_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Create a horizontal layout for the top bar
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.wallet_label)

        layout.addLayout(top_bar_layout)
        
        # --- Bet input box ---
        bet_layout = QHBoxLayout()
        bet_layout.setSpacing(8)  # Small space between widgets

        bet_label = QLabel("Enter your bet:", self)
        bet_label.setFont(QFont('Arial', 16))
        
        self.bet_input = QLineEdit(self)
        self.bet_input.setPlaceholderText("Amount")
        self.bet_input.setFixedWidth(100)  # Set the width you prefer
        
        self.bet_button = QPushButton("Place Bet", self)
        self.bet_button.setFixedWidth(90)
        self.bet_button.clicked.connect(self.place_bet)

        bet_layout.addWidget(bet_label)
        bet_layout.addWidget(self.bet_input)
        bet_layout.addWidget(self.bet_button)
        
        bet_widget = QWidget()
        
        # ---------------------
        # --- Card display area ---
        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignCenter)
        cards_layout.setSpacing(0)  # Remove space between cards
        self.card1_label = QLabel(self)
        self.card2_label = QLabel(self)
        self.card1_label.setFixedSize(80, 120)
        self.card2_label.setFixedSize(80, 120)
        self.set_cards("AS", "10H")  # Example cards
        
        cards_layout.addWidget(self.card1_label)
        cards_layout.addWidget(self.card2_label)
        
        
        
        # # --- Opponent rows ---
        # self.top_row = QHBoxLayout()
        # self.middle_row = QHBoxLayout()
        # self.bottom_row = QHBoxLayout()

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
        table_area.addWidget(self.table_cards_widget, 1, 1, alignment=Qt.AlignCenter)
        self.pot_label = QLabel("Pot: 0")
        self.pot_label.setFont(QFont('Arial',14))
        self.pot_label.setAlignment(Qt.AlignCenter)
        
        
        
        # Right opponent
        table_area.addWidget(self.opponent_widgets[2], 1, 2, alignment=Qt.AlignRight)
        # Bottom left opponent
        table_area.addWidget(self.opponent_widgets[3], 2, 0, alignment=Qt.AlignLeft)
        # Bottom right opponent
        table_area.addWidget(self.opponent_widgets[4], 2, 2, alignment=Qt.AlignRight)
        layout.addLayout(table_area)
        layout.addWidget(self.pot_label, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
        bet_widget.setLayout(bet_layout)
        layout.addWidget(bet_widget, alignment=Qt.AlignCenter)
        
        self.bet_error_label = QLabel("")
        self.bet_error_label.setStyleSheet("color: red;")
        bet_layout.addWidget(self.bet_error_label)

        layout.addLayout(cards_layout)
        self.setLayout(layout)
    
    def start_game(self):
        from game import Poker_for_GUI as PokerGame
        player_names = [self.player_name] + [f"Bot{i}" for i in range(1, self.bot_count + 1)]
        self.poker_game = PokerGame(player_names,
                                    bet_callback=self.on_bet_requested,
                                    phase_callback=self.on_phase,
                                    pot_update_callback=self.update_pot,
                                    bot_bet_update_callback=self.update_bot_bet,
                                    bot_fold_callback=self.on_bot_fold
                                    )
        self.poker_game.start_game()
    
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
    
    def place_bet(self):
        bet_value = self.bet_input.text()
        # Here you would handle the bet value (validate, update game state, etc.)
        print(f"Bet placed: {bet_value}")
        
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
        # # Show according to your layout logic
        # if num_opponents == 1:
        #     self.opponent_widgets[0].show()
        # elif num_opponents == 2:
        #     self.opponent_widgets[1].show()
        #     self.opponent_widgets[2].show()
        # elif num_opponents == 3:
        #     self.opponent_widgets[0].show()
        #     self.opponent_widgets[1].show()
        #     self.opponent_widgets[2].show()
        # elif num_opponents == 4:
        #     self.opponent_widgets[1].show()
        #     self.opponent_widgets[2].show()
        #     self.opponent_widgets[3].show()
        #     self.opponent_widgets[4].show()
        # elif num_opponents == 5:
        #     for opp in self.opponent_widgets:
        #         opp.show()
    
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
            # Update table cards display
            pass
    def update_player_cards(self, hand):
        # hand is a list like ['AS', '10H']
        self.card1_label.setPixmap(QPixmap(f"cards/{hand[0]}.png"))
        self.card2_label.setPixmap(QPixmap(f"cards/{hand[1]}.png"))
        
    def on_bet_requested(self, player, minimum_bet):
        # Show input box, wait for user to submit
        self.bet_input.setText(str(minimum_bet))
        self.bet_input.setEnabled(True)
        self.bet_button.setEnabled(True)
        
        
        try:
            self.bet_button.clicked.disconnect()
        except TypeError:
            pass  # No previous connection
        self.bet_button.clicked.connect(lambda: self.on_bet_submitted(player, minimum_bet))
        
    def on_bet_submitted(self, player, minimum_bet):
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
        if amount <= 0:
            self.bet_error_label.setText("Bet must be positive.")
            return
        
        # Valid input
        self.bet_error_label.setText("")
        player.add_to_bet(amount)
        self.bet_input.setEnabled(False)
        self.bet_button.setEnabled(False)
        self.wallet = player.wallet  # Update internal wallet value
        self.update_wallet(self.wallet)

        self.poker_game.resume_betting_round()
    
    def update_wallet(self, amount):
        self.wallet_label.setText(f"Wallet: ${amount}")
    
    def get_wallet_from_db(self, player_name):
        from game import Database_Helper as DBHelper
        db_helper = DBHelper()
        wallet = db_helper.retrieve_player_wallet(player_name)
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