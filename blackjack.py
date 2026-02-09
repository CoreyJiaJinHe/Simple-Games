
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
                 action_callback=None,
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
            
        user_player = Player(player_names[0], action_callback=action_callback, wallet=wallet)
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
        
        
        self.action_callback = action_callback
        self.phase_callback = phase_callback
        self.pot_update_callback = pot_update_callback
        self.bot_bet_update_callback = bot_bet_update_callback
        self.bot_fold_callback = bot_fold_callback
        
        self.active_players = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        self.current_player_index = 0
        self.current_hand_index = 0
        self.awaiting_initial_bet = False
        
    def deal_initial_hands(self):
        for _ in range(2):
            for player in self.players:
                player.request_card(self.dealer)
            self.dealer.deal_self()
        

    def fix_hands_and_bets(self):
        for player in self.players:
            if not player.hands:
                player.hands = [player.hand]
                player.bets = [player.bet]
    
    def show_hands(self):
        for player in self.players:
            print(f"{player.name}'s hand: {show_substituted(player.hand)}")
            
        
    def show_only_player_hand(self):
        main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        print(f"{main_player.name}'s hand: {show_substituted(main_player.hand)}")
        return main_player.hand

    def debug_hand(self):
        # Force a pair to easily test split logic
        main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        main_player.hand = ['AH', 'AD']
    
    def initial_betting_round(self):
        active_players = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        for node in active_players:
            player = node.player
            #self.pot = sum(player.bet for player in self.players)
            #wait a second, there is no pot in blackjack, just individual bets
            if player.isBot:
                bet = player.add_to_bet(self.minimum_bet)  # Bots place minimum bet for now
                bot_index=self.players.index(player)
                if self.bot_bet_update_callback:
                    self.bot_bet_update_callback(bot_index, bet)
            else:
                #Okay. This needs to be modified a little.
                if self.action_callback:
                    # Prompt GUI to collect the initial bet from the user
                    self.awaiting_initial_bet = True
                    try:
                        self.action_callback(player.name, None, options=["initial_bet"])  # bet is provided via GUI
                    except TypeError:
                        # Fallback in case the callback expects a different signature
                        self.action_callback(player.name, options=["initial_bet"])  # minimal prompt
                else:
                    # CLI fallback: set minimum bet immediately
                    player.set_bet(self.minimum_bet)
            
        if self.pot_update_callback:
            self.pot_update_callback(self.pot)
    
    def initial_bet_received(self, bet: int):
        player= next(node for node in self.player_nodes if not node.player.isBot).player
        if player.add_bet(bet):
            print(f"{player.name} has placed a bet of {bet}. Current bet: {player.current_bet}. Remaining funds: {player.wallet}")
            if self.pot_update_callback:
                self.pot_update_callback(self.pot)
        else:
            print(f"{player.name} could not place a bet of {bet} due to insufficient funds.")
            return

        # Resume round for GUI flow after receiving initial bet
        self.awaiting_initial_bet = False
        self.deal_initial_hands()
        # Keep debug_hand for split testing
        self.debug_hand()
        self.fix_hands_and_bets()
        if self.phase_callback:
            self.phase_callback("initial_deal", {"players": self.players, "dealer": self.dealer.get_hand()})
        immediate_win, immediate_result = self.check_immediate_win()
        if immediate_win:
            if immediate_result:
                win_player, winnings = immediate_result
                self.award_player(win_player, winnings)
                self.db_helper.log_game(
                    "Blackjack",
                    ', '.join([p.name for p in self.players]),
                    win_player.name,
                    winnings
                )
                self.db_helper.update_player_stats(
                    win_player.name,
                    winnings,
                    True,
                    winnings
                )
            # End round on immediate blackjack
            if self.phase_callback:
                dealerTotal = self.evaluator.evaluate_hand(self.dealer.get_hand())
                self.phase_callback("round_end", [dealerTotal, 0])
            return

        # Event-driven: prompt only the main (non-bot) player, starting with hand 0
        main_player = player
        # Ensure hands structure exists
        if not main_player.hands:
            main_player.hands = [main_player.hand]
            main_player.bets = [main_player.bet]
        self.request_player_action(main_player, 0)

    
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
    def get_action_options(self, player: Player, hand_index: int):
        if not player.hands:
            hand = player.hand
        else:
            hand = player.hands[hand_index]
        split_check = self.check_if_split_possible(hand)
        can_split = split_check and len(player.hands) < 4 and player.wallet >= player.bets[hand_index]
        options = ['hit', 'stand', 'double down', 'surrender']
        if can_split:
            options.append('split')
        return hand, options

    def request_player_action(self, player: Player, hand_index=0):
        print (f"Requesting action from {player.name} for hand {hand_index+1}...")
        if player.isBot:
        # Let the bot logic handle the action automatically
            #self.bot_play_hand(player, hand_index)
            return
        # Send phase update so GUI can highlight the active hand
        if self.phase_callback:
            self.phase_callback("player_action", {"name": player.name, "hands": player.hands if player.hands else [player.hand], "bets": player.bets if player.hands else [player.bet], "hand_index": hand_index})

        hand, options = self.get_action_options(player, hand_index)
        # Tell the GUI to prompt for action
        if self.action_callback:
            try:
                self.action_callback(player, hand_index, options)
            except TypeError:
                # Fallback to a simpler signature if needed
                self.action_callback(player, options)
        else:
            self.cli_player_action(player, hand_index)
            
        
    
    def process_player_action(self, player: Player, hand_index: int, action: str):
        if not player.hands:
            hand = player.hand
        else:
            hand = player.hands[hand_index]
        phase_action = None
        prompt_next = False
        hand_finished = False
    
        if action == 'hit':
            hand.append(self.dealer.deal_card())
            if self.evaluator.is_bust(hand):
                phase_action="bust"
                hand_finished = True
            else:
                phase_action = "hit"
                prompt_next = True
        elif action == 'stand':
            phase_action="stand"
            hand_finished = True
        elif action == 'double down':
            if player.wallet >= player.bets[hand_index]:
                player.add_to_bet(player.bets[hand_index])
                hand.append(self.dealer.deal_card())
                if self.evaluator.is_bust(hand):
                    phase_action="bust"
                    hand_finished = True
                else:
                    phase_action="double_down"
            else:
                phase_action = "funds_error"
                prompt_next = True
        elif action == 'surrender':
            refund = player.bets[hand_index] / 2
            player.surrender_bet(refund)
            phase_action="surrender"
            hand_finished = True
        elif action == 'split':
            self.handle_split(player, hand_index)
            phase_action="split"
            prompt_next = True
        else:
            phase_action = "error"
            prompt_next = True
            

        # Always notify the GUI/CLI of the state change
        #All phase actions: 
        #"hit", "stand", "double_down", "surrender", "split", "bust", "error", "funds_error"
        if self.phase_callback and phase_action:
            self.phase_callback(phase_action, {"name":player.name, "hands":player.hands, "bets":player.bets, "hand_index": hand_index})
        
        if hand_finished:
            # Move to next hand if any
            if hand_index + 1 < len(player.hands):
                print(f"Moving to next hand for {player.name}.")
                hand_index+=1
                if self.action_callback:
                    self.request_player_action(player, hand_index)
                else:
                    self.cli_player_action(player, hand_index)
                if self.phase_callback:
                    self.phase_callback("update", {"name":player.name, "hands":player.hands, "bets":player.bets, "hand_index": hand_index})
                return
            
            # Done with all hands for this player: proceed to dealer and settle
            self.dealer.play_out(self.evaluator)
            hand_results, net_winnings, dealerTotal, total_payout = self.determine_winner()
            # Award payouts to main player based on results
            main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
            main_player = main_player_node.player
            for res in hand_results:
                if res['winnings'] > 0:
                    self.award_player(main_player, res['winnings'])
            if self.phase_callback:
                self.phase_callback("round_end", [dealerTotal, net_winnings])
            # Log results
            self.db_helper.log_game(
                "Blackjack",
                ', '.join([p.name for p in self.players]),
                main_player.name,
                net_winnings
            )
            self.db_helper.update_player_stats(
                main_player.name,
                net_winnings,
                net_winnings > 0,
                total_payout
            )
            return
        # If more input is needed for the same hand (e.g., after hit or split), prompt again
        elif prompt_next:
            if self.action_callback:
                self.request_player_action(player, hand_index)
            else:
                self.cli_player_action(player, hand_index)
        # If the hand is finished, just return to let the main loop advance to the next hand/player
        



    # CLI fallback for player action
    def cli_player_action(self, player: Player, hand_index: int):
        if player.isBot:
        # Let the bot logic handle the action automatically
            #self.bot_play_hand(player, hand_index)
            return
        
        hand, options = self.get_action_options(player, hand_index)
        print(f"{player.name}'s hand: {show_substituted(hand)}. The hand total is: {self.evaluator.evaluate_hand(hand)}")
        print(f"Options: {', '.join(options)}")
        action = input("Choose action: ").strip().lower()
        self.process_player_action(player, hand_index, action)
    
    
    # def decide_player_actions(self, player: Player):

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
            #print("DEBUG split check:", card1, remove_suit([card1]), card2, remove_suit([card2]))
            if remove_suit([card1])[0] == remove_suit([card2])[0]:
                return True
        return False
    
    def prompt_next_action(self):
        # Retained for future multi-player support; not used in main-player-only flow
        if not self.active_players:
            return
        player = self.active_players[self.current_player_index].player
        self.request_player_action(player, self.current_hand_index)
    
    
    
    def start_game(self):
        # Begin with initial betting round. In GUI mode, pause until initial_bet_received is called.
        self.initial_betting_round()
        if self.action_callback:
            # GUI: wait for initial_bet_received to continue
            return

        # CLI flow continues immediately
        self.deal_initial_hands()
        # Keep debug_hand for split testing
        self.debug_hand()
        self.fix_hands_and_bets()
        if self.phase_callback:
            self.phase_callback("initial_deal", {"players": self.players, "dealer": self.dealer.get_hand()})

        immediate_win, immediate_result = self.check_immediate_win()
        if immediate_win:
            if immediate_result:
                win_player, winnings = immediate_result
                self.award_player(win_player, winnings)
                self.db_helper.log_game(
                    "Blackjack",
                    ', '.join([p.name for p in self.players]),
                    win_player.name,
                    winnings
                )
                self.db_helper.update_player_stats(
                    win_player.name,
                    winnings,
                    True,
                    winnings
                )
            if self.phase_callback:
                dealerTotal = self.evaluator.evaluate_hand(self.dealer.get_hand())
                self.phase_callback("round_end", [dealerTotal, 0])
            return

        # Only prompt the main player (non-bot)
        main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        if not main_player.hands:
            main_player.hands = [main_player.hand]
            main_player.bets = [main_player.bet]

        self.request_player_action(main_player, 0)
        

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