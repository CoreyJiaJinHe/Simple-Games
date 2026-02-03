
from Database_Helper import Database_Helper
from Dealer import Dealer
from HandEvaluators import BlackjackHandEvaluator
from Player import Player
from utils import show_substituted

class BlackjackDealer(Dealer):
    def __init__(self):
        super().__init__()
    

class BlackJack():
    def __init__(self, player_names,
                 bet_callback=None,
                 phase_callback=None,
                 pot_update_callback=None,
                 bot_bet_update_callback=None,
                 bot_fold_callback=None):
        self.dealer = BlackjackDealer()
        self.evaluator = BlackjackHandEvaluator()
        self.db_helper= Database_Helper()
    
        wallet = self.db_helper.retrieve_player_wallet(player_names[0])
        override = False
        if override:
            wallet = 1000
        elif wallet is None:
            wallet = 1000 #Default
        elif wallet <= 0:
            self.db_helper.player_take_loan(player_names[0])
            
        user_player = Player(player_names[0], bet_callback=bet_callback, wallet=wallet)
        self.players = [user_player]
        
        self.dealt = []
        self.pot = 0
        self.minimum_bet = 10
        
        
        self.bet_callback = bet_callback
        self.phase_callback = phase_callback
        self.pot_update_callback = pot_update_callback
        self.bot_bet_update_callback = bot_bet_update_callback
        self.bot_fold_callback = bot_fold_callback
        
    def deal_initial_hands(self):
        for _ in range(2):
            for player in self.players:
                player.request_card(self.dealer)
                self.dealer.deal_self()
        
    def show_hands(self):
        for player in self.players:
            print(f"{player.name}'s hand: {show_substituted(player.hand)}")
    
    def show_only_player_hand(self):
        main_player = self.players[0]  # First player is always the human
        print(f"{main_player.name}'s hand: {show_substituted(main_player.hand)}")
        return main_player.hand
    
    def initial_betting_round(self):
        for player in self.players:
            self.pot = sum(node.player.bet for node in self.player_nodes)
            if player.isBot:
                bet = player.place_bet(self.minimum_bet)  # Bots place minimum bet for now
                if self.bot_bet_update_callback:
                    self.bot_bet_update_callback(player.name, bet)
            else:
                if self.bet_callback:
                    self.bet_callback(player.name, bet)
                else:
                    bet = player.set_bet(self.minimum_bet)
            
        if self.pot_update_callback:
            self.pot_update_callback(self.pot)
    
    def check_immediate_win(self):
        dealer_blackjack =self.evaluator.is_blackjack(self.dealer.hand)
        if (dealer_blackjack):
            print ("Dealer has blackjack!")
            for player in self.players:
                player_blackjack = self.evaluator.is_blackjack(player.hand)
                if player_blackjack:
                    print(f"{player.name} also has blackjack! It's a push.")
                    #Push, return bet
                    player.wallet += player.bet
                else:
                    print(f"{player.name} loses to dealer blackjack.")
                    #Dealer wins, take bet
                    pass
            return True
        else:
            for player in self.players:
                player_blackjack = self.evaluator.is_blackjack(player.hand)
                if player_blackjack:
                    print(f"{player.name} has blackjack and wins 1.5x their bet!")
                    player.win_bet(1.5*player.bet+player.bet)
                    self.players.remove(player)  # Remove player from further play
                    if not (player.isBot):
                        return True  # Game over for human player
        
        return False  # No immediate win, continue game
    
    def decide_player_actions(self, player):
        split_check=self.check_if_split_possible(player)
        if not player.isBot:
            while True:
                if self.bet_callback:
                    # The callback should handle getting the action from the GUI and call back into this logic
                    # For GUI, you might want to break here and let the callback resume the logic
                    self.bet_callback(player)
                    break
                else:
                    options = ['hit', 'stand', 'double down', 'surrender']
                    if split_check:
                        options.append('split')
                    action = input(f"Choose action ({', '.join(options)}): ").strip().lower()
                
                if action == 'hit':
                    player.request_card(self.dealer)
                    if self.evaluator.is_bust(player.hand):
                        print(f"{player.name} busts with hand: {show_substituted(player.hand)}")
                        break
                elif action == 'stand':
                    print(f"{player.name} stands with hand: {show_substituted(player.hand)}")
                    break
                elif action == 'double down':
                    if player.wallet >= player.bet:
                        player.add_to_bet(player.bet)
                        player.request_card(self.dealer)
                        print(f"{player.name} doubles down and receives a card: {show_substituted(player.hand)}")
                        if self.evaluator.is_bust(player.hand):
                            print(f"{player.name} busts with hand: {show_substituted(player.hand)}")
                        break
                    else:
                        print(f"{player.name} does not have enough funds to double down.")
                elif action == 'surrender':
                    refund = player.bet / 2
                    player.wallet += refund
                    print(f"{player.name} surrenders and gets back {refund}.")
                    break
                elif action == 'split' and split_check:
                    # Handle split logic here
                    self.handle_split(player)
                    break
                else:
                    print("Invalid action. Please choose again.")
    def handle_split(self, player):
        card1, card2 = player.hand
        if player.wallet < player.bet:
            print("Not enough funds to split.")
            return
        # Remove the original hand and bet
        player.hands = []
        player.bets = []
        # Create two hands, each with one card, and place a bet for each
        player.hands.append([card1])
        player.hands.append([card2])
        player.bets.append(player.bet)
        player.bets.append(player.bet)
        player.wallet -= player.bet  # Deduct the second bet

        # Deal one card to each new hand
        for hand in player.hands:
            hand.append(self.dealer.deal_card())

        print(f"{player.name} splits: {player.hands}")
        # Let the player act on each hand immediately after splitting
        for i, hand in enumerate(player.hands):
            print(f"Playing hand {i+1}: {show_substituted(hand)}")
            self.decide_player_actions_for_hand(player, hand, i)
        
    def decide_player_actions_for_hand(self, player, hand, hand_index):
        split_check=self.check_if_split_possible(player)
        if not player.isBot:
            while True:
                if self.bet_callback:
                    # The callback should handle getting the action from the GUI and call back into this logic
                    # For GUI, you might want to break here and let the callback resume the logic
                    self.bet_callback(player)
                    break
                else:
                    options = ['hit', 'stand', 'double down', 'surrender']
                    if split_check:
                        options.append('split')
                    action = input(f"Choose action ({', '.join(options)}): ").strip().lower()
                
                if action == 'hit':
                    player.hands[hand_index].append(self.dealer.deal_card())
                    if self.evaluator.is_bust(player.hands[hand_index]):
                        print(f"{player.name} busts with hand: {show_substituted(player.hands[hand_index])}")
                        break
                elif action == 'stand':
                    print(f"{player.name} stands with hand: {show_substituted(player.hands[hand_index])}")
                    break
                elif action == 'double down':
                    if player.wallet >= player.bets[hand_index]:
                        player.add_to_bet(player.bets[hand_index])
                        player.hands[hand_index].append(self.dealer.deal_card())
                        print(f"{player.name} doubles down and receives a card: {show_substituted(player.hands[hand_index])}")
                        if self.evaluator.is_bust(player.hands[hand_index]):
                            print(f"{player.name} busts with hand: {show_substituted(player.hands[hand_index])}")
                        break
                    else:
                        print(f"{player.name} does not have enough funds to double down.")
                elif action == 'surrender':
                    refund = player.bets[hand_index] / 2
                    player.wallet += refund
                    print(f"{player.name} surrenders and gets back {refund}.")
                    break
                elif action == 'split' and split_check:
                    # Handle split logic here
                    self.handle_split(player)
                    break
                else:
                    print("Invalid action. Please choose again.")
        
        
        
    def check_if_split_possible(self, player):
        if len(player.hand) == 2:
            card1, card2 = player.hand
            if card1.rank == card2.rank:
                return True
        return False
    
    
    def start_game(self):
        #Get players to place an initial bet
        self.initial_betting_round()
        
        #Then deal cards clockwise/counterclockwise.
        self.deal_initial_hands()
        self.show_only_player_hand()
        
        #If Dealer card is Ace, ask if players want 'insurance'
        #'insurance' is a bet if the Dealer has blackjack. If so, pay 2:1 on insurance bet.
        #If Dealer doesn't, lose insurance bet.
        #If Player has blackjack as well, nothing happens. Everyone keeps their bet.
        #Dealer wins otherwise.
        immediate_win=self.check_immediate_win()
        if immediate_win:
            print("Game over. Play again?")
            return
            
        #After cards are dealt, check for blackjack among all players.
        #If dealer has blackjack, game ends. If player has blackjack, they win 1.5x their bet if dealer can't match.
        #If not, play normally.
        
        #Ask player if they want to hit, stand, doubledown or surrender.
        #If they have a pair, they may split their hand into two. They must match the initial bet for the new hand.
        #Hit is get a card, no additional bets.
        #Doubledown is get a card, double the bet.
        #Surrender is give up half the bet, end turn.
        #Stand is end turn.
        
        for player in self.players:
            if player.hands:
                for i, hand in enumerate(player.hands):
                    print(f"Playing hand {i+1}: {show_substituted(hand)}")
                    # Let the player act on each hand (hit/stand/etc.)
                    self.decide_player_actions_for_hand(player, hand, i)
            else:
                self.decide_player_actions(player)
        
        
        #After player is done, dealer reveals hidden card and hits until they reach 17 or higher.
        
    