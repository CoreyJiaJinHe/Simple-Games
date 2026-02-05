
from Database_Helper import Database_Helper
from Dealer import Dealer
from HandEvaluators import BlackjackHandEvaluator
from Player import BotPlayer, Player
from utils import remove_suit, show_substituted
class PlayerNode:
    def __init__(self, player):
        self.player = player
        self.next = None
        self.prev = None
        
class BlackjackDealer(Dealer):
    def __init__(self):
        super().__init__()
    
    def play_out(self,evaluator: BlackjackHandEvaluator):
        while True:
            hand_value = evaluator.evaluate_hand(self.get_hand())
            #print(hand_value)
            if hand_value < 17:
                card=self.deal_self_return()
                hand_value= evaluator.evaluate_hand(self.get_hand())
                print(f"Dealer hits and receives: {show_substituted(card)}. They are now at {hand_value}.")
            elif hand_value > 21:
                print("Dealer busts with hand:", show_substituted(self.get_hand()))
                return False
            else:
                print("Dealer stands with hand:", show_substituted(self.get_hand()))
                break
        
    def debug_show_dealer_hand(self):
        print(f"Dealer's hand: {show_substituted(self.get_hand())}")

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
        bot_players = [BotPlayer(f"Bot{i}", game_type="Blackjack") for i in range(1, len(player_names))]
        self.players = bot_players + [user_player]
        # Create circular linked list of players
        self.player_nodes = [PlayerNode(p) for p in self.players]
        n = len(self.player_nodes)
        for i in range(n):
            self.player_nodes[i].next = self.player_nodes[(i+1)%n]
            self.player_nodes[i].prev = self.player_nodes[(i-1)%n]
            
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
        main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        print(f"{main_player.name}'s hand: {show_substituted(main_player.hand)}")
        return main_player.hand
    
    def initial_betting_round(self):
        active_players = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        for node in active_players:
            player = node.player
            #self.pot = sum(player.bet for player in self.players)
            #wait a second, there is no pot in blackjack, just individual bets
            if player.isBot:
                bet = player.add_to_bet(self.minimum_bet)  # Bots place minimum bet for now
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
        immediate_result = None  # Will hold (player, winnings) if a player wins
        if dealer_blackjack:
            print("Dealer has blackjack!")
            for player in self.players:
                player_blackjack = self.evaluator.is_blackjack(player.hand)
                if player_blackjack:
                    print(f"{player.name} also has blackjack! It's a push.")
                    player.return_bet()
                else:
                    print(f"{player.name} loses to dealer blackjack.")
            return True, None
        else:
            for player in self.players:
                player_blackjack = self.evaluator.is_blackjack(player.hand)
                if player_blackjack:
                    winnings = 1.5 * player.bet + player.bet
                    print(f"{player.name} has blackjack and wins 1.5x their bet!")
                    immediate_result = (player, winnings)
                    self.players.remove(player)  # Remove player from further play
                    if not player.isBot:
                        return True, immediate_result
        return False, None
    
    def decide_player_actions(self, player: Player):
        # Ensure player.hands is always a list of hands
        if not hasattr(player, 'hands') or not player.hands:
            player.hands = [player.hand]
            player.bets = [player.bet]
        
        for i, hand in enumerate(player.hands):
            split_check=self.check_if_split_possible(hand)
            can_split = split_check and len(player.hands) < 4 and player.wallet >= player.bets[i]
            if not player.isBot:
                while True:
                    if self.bet_callback:
                        # The callback should handle getting the action from the GUI and call back into this logic
                        # For GUI, you might want to break here and let the callback resume the logic
                        self.bet_callback(player)
                        break
                    else:
                        if self.evaluator.is_bust(hand):
                            break
                        print(f"{player.name}'s hand: {show_substituted(hand)}")
                        total= self.evaluator.evaluate_hand(hand)
                        print(f"{player.name}'s hand total is: {total}")
                        options = ['hit', 'stand', 'double down', 'surrender']
                        if can_split:
                            options.append('split')
                        action = input(
                            f"Playing hand {i+1}: {show_substituted(hand)}\nChoose action ({', '
                            .join(options)}): ").strip().lower()
                        if action == 'hit':
                            player.hands[i].append(self.dealer.deal_card())
                        elif action == 'stand':
                            print(f"{player.name} stands with hand: {show_substituted(hand)}")
                            break
                        elif action == 'double down':
                            if player.wallet >= player.bets[i]:
                                player.add_to_bet(player.bets[i])
                                player.hands[i].append(self.dealer.deal_card())
                                print(f"{player.name} doubles down and receives a card: {show_substituted(hand)}")
                            else:
                                print(f"{player.name} does not have enough funds to double down.")
                        elif action == 'surrender':
                            refund = player.bets[i] / 2
                            player.surrender_bet(refund)
                            print(f"{player.name} surrenders and gets back {refund}.")
                            break
                        elif action == 'split' and can_split:
                            # Handle split logic here
                            self.handle_split(player,i)
                            print("Player has split their hand.")
                            return self.decide_player_actions(player)
                        else:
                            print("Invalid action. Please choose again.")
                if self.evaluator.is_bust(hand):
                    print(f"{player.name} bust with hand: {show_substituted(hand)}")
    
    def handle_split(self, player: Player, hand_index: int):
        hand = player.hands[hand_index]
        if len(hand) != 2 or player.wallet < player.bets[hand_index]:
            print("Cannot split this hand.")
            return

        card1, card2 = hand
        # Remove the original hand and bet
        player.hands.pop(hand_index)
        bet = player.bets.pop(hand_index)

        # Create two new hands, each with one card, and place a bet for each
        player.hands.insert(hand_index, [card2])
        player.hands.insert(hand_index, [card1])
        player.bets.insert(hand_index, bet)
        player.bets.insert(hand_index, bet)
        player.add_bet(bet)  # Deduct the additional bet

        # Deal one card to each new hand
        player.hands[hand_index].append(self.dealer.deal_card())
        player.hands[hand_index + 1].append(self.dealer.deal_card())

        print(f"{player.name} splits: {player.hands}")

    def check_if_split_possible(self, hand):
        if len(hand) == 2:
            card1, card2 = hand
            if remove_suit([card1])[0] == remove_suit([card2])[0]:
                return True
        return False
    
    
    def start_game(self):
        #Get players to place an initial bet
        self.initial_betting_round()
        
        #Then deal cards clockwise/counterclockwise.
        self.deal_initial_hands()
        def debug_hand():
            main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
            main_player = main_player_node.player
            main_player.hand=['AH','AD']
        debug_hand()
        self.show_only_player_hand()
        
        #self.show_hands()
        
        self.dealer.debug_show_dealer_hand()
        #If Dealer card is Ace, ask if players want 'insurance'
        #'insurance' is a bet if the Dealer has blackjack. If so, pay 2:1 on insurance bet.
        #If Dealer doesn't, lose insurance bet.
        #If Player has blackjack as well, nothing happens. Everyone keeps their bet.
        #Dealer wins otherwise.
        immediate_win, immediate_result = self.check_immediate_win()
        if immediate_win:
            if immediate_result:
                player, winnings = immediate_result
                self.award_player(player, winnings)
                self.db_helper.log_game(
                    "Blackjack",
                    ', '.join([p.name for p in self.players]),
                    player.name,
                    winnings
                )
                self.db_helper.update_player_stats(
                    player.name,
                    winnings,
                    True,
                    winnings
                )
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
        active_players = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        for node in active_players:
            player = node.player
            self.decide_player_actions(player)
        
        
        #After player is done, dealer reveals hidden card and hits until they reach 17 or higher.
        self.dealer.play_out(self.evaluator)
        hand_results, net_winnings, dealerTotal, total_payout = self.determine_winner()
        if self.phase_callback:
            self.phase_callback("round_end", [dealerTotal, net_winnings])

        for i, hand_result in enumerate(hand_results):
            if hand_result['result'] == 'win':
                self.award_player(player, hand_result['bet'] * 2)
            elif hand_result['result'] == 'push':
                self.award_player(player, hand_result['bet'])

        self.db_helper.log_game(
            "Blackjack",
            ', '.join([p.name for p in self.players]),
            player.name,
            net_winnings
        )
        self.db_helper.update_player_stats(
            player.name,
            net_winnings,                # profit/loss
            net_winnings > 0,            # won_game
            total_payout                 # total payout (bets returned + winnings)
        )
        print("Game over. Play again?")
        

    def determine_winner(self):
        dealerTotal = self.evaluator.evaluate_hand(self.dealer.get_hand())
        player_node = next(node for node in self.player_nodes if not node.player.isBot)
        player = player_node.player
        hand_results = []
        net_winnings = 0
        total_payout = 0

        if player.hands:
            for i, hand in enumerate(player.hands):
                print(f"Evaluating for hand {i+1}: {show_substituted(hand)}")
                playerTotal = self.evaluator.evaluate_hand(hand)
                result = None
                winnings = 0
                if playerTotal > dealerTotal or dealerTotal > 21:
                    result = 'win'
                    winnings = player.bets[i] * 2
                    net_winnings += player.bets[i]
                    print(f"For hand {i+1}, {player.name} wins with total {playerTotal} against dealer's {dealerTotal}! Wins {winnings}.")
                elif playerTotal == dealerTotal:
                    result = 'push'
                    winnings = player.bets[i]  # bet returned
                    print(f"For hand {i+1}, {player.name} pushes with total {playerTotal} against dealer's {dealerTotal}. Bet returned.")
                else:
                    result = 'lose'
                    winnings = 0
                    net_winnings -= player.bets[i]
                    print(f"For hand {i+1}, {player.name} loses with total {playerTotal} against dealer's {dealerTotal}.")
                total_payout += winnings
                hand_results.append({'result': result, 'bet': player.bets[i], 'winnings': winnings})
        else:
            playerTotal = self.evaluator.evaluate_hand(player.hand)
            if playerTotal > dealerTotal or dealerTotal > 21:
                net_winnings = player.bet
                total_payout = player.bet * 2
                print(f"{player.name} wins with total {playerTotal} against dealer's {dealerTotal}! Wins {player.bet * 2}.")
            elif playerTotal == dealerTotal:
                total_payout = player.bet
                print(f"{player.name} pushes with total {playerTotal} against dealer's {dealerTotal}. Bet returned.")
            else:
                net_winnings = -player.bet
                total_payout = 0
                print(f"{player.name} loses with total {playerTotal} against dealer's {dealerTotal}.")

        # Return overall result
        return hand_results, net_winnings, dealerTotal, total_payout    
    def award_player(self,player : Player,bet: int):
        player.win_bet(bet)
        
    def determine_bot_winners(self):
        dealerTotal = self.evaluator.evaluate_hand(self.dealer.get_hand())
        winners = []
        for node in self.player_nodes:
            player = node.player
            if player.isBot:
                if player.hands:
                    for hand in player.hands:
                        playerTotal = self.evaluator.evaluate_hand(hand)
                        if playerTotal > dealerTotal or dealerTotal > 21:
                            winners.append(player.name)
                else:
                    playerTotal = self.evaluator.evaluate_hand(player.hand)
                    if playerTotal > dealerTotal or dealerTotal > 21:
                        winners.append(player.name)
        return winners
        
if __name__ == "__main__":
    game = BlackJack(player_names=["You", "Bot1", "Bot2"])
    game.start_game()