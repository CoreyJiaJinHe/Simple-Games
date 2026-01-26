from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget, QLineEdit, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QPixmap, QKeySequence
from PyQt5.QtWidgets import QShortcut

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

    def show_game_screen(self):
        self.stacked_widget.setCurrentWidget(self.game_screen)


class GameScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # --- Bet input box ---
        bet_layout = QHBoxLayout()
        bet_layout.setSpacing(8)  # Small space between widgets

        bet_label = QLabel("Enter your bet:", self)
        bet_label.setFont(QFont('Arial', 16))
        
        self.bet_input = QLineEdit(self)
        self.bet_input.setPlaceholderText("Amount")
        self.bet_input.setFixedWidth(100)  # Set the width you prefer
        
        bet_button = QPushButton("Place Bet", self)
        bet_button.setFixedWidth(90)
        bet_button.clicked.connect(self.place_bet)

        bet_layout.addWidget(bet_label)
        bet_layout.addWidget(self.bet_input)
        bet_layout.addWidget(bet_button)
        
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
        # Right opponent
        table_area.addWidget(self.opponent_widgets[2], 1, 2, alignment=Qt.AlignRight)
        # Bottom left opponent
        table_area.addWidget(self.opponent_widgets[3], 2, 0, alignment=Qt.AlignLeft)
        # Bottom right opponent
        table_area.addWidget(self.opponent_widgets[4], 2, 2, alignment=Qt.AlignRight)
        layout.addLayout(table_area)
        
        
        self.setLayout(layout)
        self.update_opponents(num_opponents=5)  # Example number of opponents
        
        
        
        bet_widget.setLayout(bet_layout)
        layout.addWidget(bet_widget, alignment=Qt.AlignCenter)
        layout.addLayout(cards_layout)
        self.setLayout(layout)
    
    # def resizeEvent(self, event):
    #     new_width = max(0, self.width() - 200)
    #     self.middle_row_widget.setMaximumWidth(new_width)
    #     #self.middle_row_widget.setMinimumWidth(0)
    #     super().resizeEvent(event)
        
        
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
        label = QLabel(name)
        card1 = QLabel()
        card2 = QLabel()
        card1.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        card2.setPixmap(QPixmap("cards_graphic/card_back.png").scaled(40, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        hbox = QHBoxLayout()
        hbox.addWidget(card1)
        hbox.addWidget(card2)
        vbox.addWidget(label, alignment=Qt.AlignCenter)
        vbox.addLayout(hbox)
        widget.setLayout(vbox)
        return widget

    def update_opponents(self, num_opponents):
        # Hide all first
        for opp in self.opponent_widgets:
            opp.hide()
        # Show according to your layout logic
        if num_opponents == 1:
            self.opponent_widgets[0].show()
        elif num_opponents == 2:
            self.opponent_widgets[1].show()
            self.opponent_widgets[2].show()
        elif num_opponents == 3:
            self.opponent_widgets[0].show()
            self.opponent_widgets[1].show()
            self.opponent_widgets[2].show()
        elif num_opponents == 4:
            self.opponent_widgets[1].show()
            self.opponent_widgets[2].show()
            self.opponent_widgets[3].show()
            self.opponent_widgets[4].show()
        elif num_opponents == 5:
            for opp in self.opponent_widgets:
                opp.show()
    
    
    
class WelcomeScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.setWindowTitle('Poker Game')
        
        self.resize(600,300)
        
        layout = QVBoxLayout()

        titleLabel = QLabel('Welcome to Poker!', self)
        titleLabel.setFont(QFont('Times New Roman', 64))
        startButton = QPushButton('Start Game', self)
        startButton.clicked.connect(switch_callback)
        
        startButton.clicked.connect(self.on_start_game)

        layout.addWidget(titleLabel, alignment=Qt.AlignCenter)
        layout.addWidget(startButton, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        
    def on_start_game(self):
        from game import game_start
        #game_start()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()