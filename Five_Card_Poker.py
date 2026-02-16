
from Database_Helper import Database_Helper
from Dealer import Dealer
from HandEvaluators import PokerHandEvaluator
from Player import BotPlayer, Player
from utils import show_substituted

class PlayerNode:
    def __init__(self, player):
        self.player = player
        self.next = None
        self.prev = None
    
    def add_player(self, new_player):
        new_node = PlayerNode(new_player)
        if self.next is None:  # First player being added
            self.next = new_node
            self.prev = new_node
            new_node.next = self
            new_node.prev = self
        else:
            new_node.prev = self.prev
            new_node.next = self
            self.prev.next = new_node
            self.prev = new_node

class FiveCardPoker():
    def __init__(self, player_names, 
                 action_callback=None, #Callback to request bet from GUI
                 phase_callback=None, #Callback to notify GUI of phase changes
                 pot_update_callback=None, #Updates the pot label on the GUI
                 bot_bet_update_callback=None, #Updates the bot bet label on the GUI
                 bot_fold_callback=None): #Notifies GUI that a bot has folded and shows their cards
        self.db_helper = Database_Helper()
        self.dealer = Dealer()
        self.evaluator = PokerHandEvaluator()

        wallet = self.db_helper.retrieve_player_wallet(player_names[0])
        override = False
        if override:
            wallet = 1000
        elif wallet is None:
            wallet = 1000 #Default
        elif wallet <= 0:
            self.db_helper.player_take_loan(player_names[0])
        
        user_player = Player(player_names[0], action_callback=action_callback, wallet=wallet)
        bot_players = [BotPlayer(f"Bot{i}", game_type="Poker") for i in range(1, len(player_names))]
        self.players = [user_player] + bot_players
        #print(f"Initialized players: {[p.name for p in self.players]} with wallets: {[p.wallet for p in self.players]}")
        # Create circular linked list of players
        self.player_nodes = [PlayerNode(p) for p in self.players]
        n = len(self.player_nodes)
        for i in range(n):
            self.player_nodes[i].next = self.player_nodes[(i+1)%n]
            self.player_nodes[i].prev = self.player_nodes[(i-1)%n]
            
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_round_number = 0
        
        
        self.action_callback = action_callback
        self.phase_callback = phase_callback
        self.pot_update_callback = pot_update_callback
        self.bot_bet_update_callback = bot_bet_update_callback
        self.bot_fold_callback = bot_fold_callback
        
        self._betting_need_to_act = None
        self._betting_current_bet = None
        self._betting_done_callback = None
        
    def get_main_player_node(self):
        # Helper to retrieve the non-bot (human) player's node
        return next(node for node in self.player_nodes if not node.player.isBot)

    def get_main_player(self):
        # Helper to retrieve the non-bot (human) player
        return self.get_main_player_node().player

    def deal_initial_hands(self):
        # Deal cards in a circle, one at a time, until everyone has 5 cards.
        for _ in range(5):
            for node in self.player_nodes:
                card = self.dealer.deal_card()
                node.player.hand.append(card)

    def discard_phase(self):
        # Ask each player how many cards they want to discard, then which ones, then deal new cards to those who discarded.
        for node in self.player_nodes:
            player = node.player
            if player.isBot:
                break
                num_to_discard = player.decide_discard(self.hand_evaluator)
                if num_to_discard > 0:
                    indices_to_discard = player.choose_discard_indices(num_to_discard)
                    for index in sorted(indices_to_discard, reverse=True):
                        player.discard_card(self.dealer, index)

            else:
                if self.action_callback:
                    num_to_discard = self.action_callback("discard_count_phase", player.name, "discard_count")
                else:
                    num_to_discard = int(input(f"{player.name}, how many cards would you like to discard? (0-3): "))
                if num_to_discard > 0:
                    if (self.action_callback):
                        indices_to_discard = self.action_callback("cards_to_discard_phase", player.name, num_to_discard)
                    else:
                        indices_to_discard = input(f"Which card indices would you like to discard? (0-{len(player.hand)-1}, separate by commas): ")
                        indices_to_discard = [int(idx.strip()) for idx in indices_to_discard.split(",")]
                    for index in sorted(indices_to_discard, reverse=True):
                        player.discard_card(self.dealer, index)
        if (self.phase_callback):
            self.phase_callback("deal_new_cards")
        self.deal_new_cards()
        
    def deal_new_cards(self):
        #We need to loop through the players again and deal new cards to those who discarded. 
        # We can track this by counting hand_sizes. If the player's hand is not five cards, we know they discarded and need to be dealt new cards until they have five again.
        start_node = self.get_main_player_node()
        current_node = start_node
        isDone= False
        while isDone == False:
            if all(len(node.player.hand) == 5 for node in self.player_nodes):
                isDone = True
            else:
                current_player = current_node.player
                if len(current_player.hand) < 5:
                    current_player.request_card(self.dealer)
                current_node = current_node.next
        print("All players have 5 cards again. Ending deal phase.")
        if (self.phase_callback):
            self.phase_callback("update_hands", self.players)
            #self.action_callback("final_betting_round")
            
        self.betting_round(minimum_bet=10, round_name="final_betting_round")
    
    def get_ordered_active_nodes_after(self, raiser_node):
        result = []
        node = raiser_node.next
        while node != raiser_node:
            if not node.player.isFolded and node.player.wallet > 0:
                result.append(node)
            node = node.next
        return result
    
    def bot_set_bet(self, player, to_call, round_number):
        pass
    
    def betting_round(self, minimum_bet=10, round_name="betting_round"):
        # Set round_number based on round_name if not already set
        if round_name == "initial_betting_round":
            self.current_round_number = 1
        elif round_name == "final_betting_round":
            self.current_round_number = 2
        # Initialize betting state
        self._betting_current_bet = minimum_bet
        
        self._betting_need_to_act = [node for node in self.player_nodes if not node.player.isFolded and node.player.wallet > 0]
        
        self._betting_done_callback = None
        
        def done_callback():
            self.pot = sum(node.player.bet for node in self.player_nodes)
            print(f"Total pot is now: {self.pot}\n")
            if self.pot_update_callback:
                self.pot_update_callback(self.pot)
            if self.current_round_number == 1:
                self.discard_phase()
            elif self.current_round_number == 2:
                self.showdown()

        self._betting_done_callback = done_callback
        self.betting_next()
    
    def betting_next(self):
        # If no one left to act, finish the betting round
        if not self._betting_need_to_act:
            self.pot = sum(node.player.bet for node in self.player_nodes)
            #print(f"Total pot is now: {self.pot}\n")
            if self._betting_done_callback:
                self._betting_done_callback()
            return

        node = self._betting_need_to_act.pop(0)
        player = node.player
        if player.isFolded or player.wallet <= 0:
            self.betting_next()
            return
        if self._betting_current_bet > 0 and player.current_bet == self._betting_current_bet:
            self.betting_next()
            return

        to_call = max(0, self._betting_current_bet - player.current_bet)
        print(f"{player.name}'s turn. Current bet to call: {to_call}. Wallet: {player.wallet}")

        #wallet_before = player.wallet
        if player.isBot:
            self.bot_set_bet(player, to_call, round_number=self.current_round_number)
            bot_index = self.players.index(player) - 1  # Adjust for human player at index 0
            # Check to see if the bot folds before updating wallet/pot/callbacks
            if player.isFolded:
                if self.bot_fold_callback:
                    self.bot_fold_callback(bot_index, hand=player.hand)
                # Skip wallet/pot/bet updates for folded bot
                self.betting_next()
                return
            #wallet_after = player.wallet
            #delta = wallet_after - wallet_before
            self.pot = sum(node.player.bet for node in self.player_nodes)
            if self.pot_update_callback:
                self.pot_update_callback(self.pot)
            if self.bot_bet_update_callback:
                self.bot_bet_update_callback(bot_index, player.current_bet)
            #self.db_helper.update_player_wallet(player.name, delta)
            if player.current_bet > self._betting_current_bet:
                # Update the current bet and requeue all others except this player
                self._betting_current_bet = player.current_bet
                self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
            self.betting_next()
        else:
            # For human, call the callback and wait for GUI to resume
            if self.action_callback:
                self._last_human_node = node  # Save for resume
                self._last_human_bet = player.current_bet  # Save for resume
                self.action_callback("to_call", to_call)
            else:
                player.set_bet(to_call)
                if player.current_bet > self._betting_current_bet:
                    # Update the current bet and requeue all others except this player
                    self._betting_current_bet = player.current_bet
                    self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
                self.betting_next()
            # Wait for GUI to call resume_betting_round()
    
    def showdown(self):
        print(f"The final pot total is: {self.pot}\n")
        self.show_hands()
        self.determine_winner()
    
    def award_player(self,player : Player,bet: int):
        player.win_bet(bet)
    
    def determine_winner(self):
        winner= None
        highest_rank=0
        winning_hand=[]
        players = [p for p in self.players if not p.isFolded]
        for player in players:
            hand = player.hand
            print (hand)
            rank, result, hand_name = self.evaluator.evaluate_hand(hand, [])
            print(f"{player.name} has {hand_name}: {show_substituted(result)}")
            if rank > highest_rank:
                highest_rank = rank
                winner = player
                winning_hand = result
        if self.phase_callback:
            self.phase_callback("winner", [winner.name,winning_hand,self.pot])
        print(f"The winner is {winner.name} with hand: {show_substituted(winning_hand)}")
        self.award_player(winner, self.pot)
        self.db_helper.log_game("Poker", ', '.join([p.name for p in players]), winner.name, self.pot)
        self.db_helper.update_player_stats(winner.name, self.pot, True, self.pot)
    
    def start_game(self):
        
        
        #Five Card Poker.
        #Get initial buy in bets.
        #Deal cards in a circle, one at a time, until everyone has 5 cards.
        
        self.deal_initial_hands()
        
        self.show_only_player_hand()
        
        #self.show_hands()
        self.betting_round(minimum_bet=10, round_name="initial_betting_round")
        #Now figure out who wants to discard cards. Can discard up to three.
        #Cards are discarded simultaneously, so we ask each player how many cards they want to discard, 
        #Then we go around again and ask which ones.
        #After discarding, we deal new cards to those who discarded, again in a circle, one at a time.
        #Then we do a final betting round, then reveal hands and determine winner
        #self.discard_phase()
        
        
        
    def show_hands(self):
        for player in self.players:
            print(f"{player.name}'s hand: {show_substituted(player.hand)}")
            
    def show_only_player_hand(self):
        main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        print(f"{main_player.name}'s hand: {show_substituted(main_player.hand)}")
        #return main_player.hand

if "__main__" == __name__:
    game = FiveCardPoker(player_names=["You", "Bot1", "Bot2"])
    game.start_game()



















    # def initial_betting_round(self):
    #     for node in self.player_nodes:
    #         player = node.player
    #         if player.isBot:
    #             bet_amount = player.decide_bet(self.current_bet, self.pot, self.hand_evaluator)
    #             if bet_amount > 0:
    #                 player.add_bet(bet_amount)
    #                 if self.bot_bet_update_callback:
    #                     self.bot_bet_update_callback(player.name, bet_amount)
    #         else:
    #             if self.action_callback:
    #                 bet_amount = self.action_callback("initial_betting_round")
    #                 if bet_amount > 0:
    #                     if player.add_bet(bet_amount):
    #                         if self.pot_update_callback:
    #                             self.pot_update_callback(self.pot)
    #                     else:
    #                         print(f"{player.name} does not have enough funds to bet {bet_amount}.")
    #             else:
    #                 bet_amount = int(input(f"{player.name}, how much would you like to bet? Current pot is {self.pot}: "))
    #                 if bet_amount > 0:
    #                     player.set_bet(bet_amount)

    #         self.pot = sum(node.player.bet for node in self.player_nodes)
    #     if (self.pot_update_callback):
    #         self.pot_update_callback(self.pot)
    
    # def final_betting_round(self):
    #     for node in self.player_nodes:
    #         player = node.player
    #         if player.isBot:
    #             bet_amount = player.decide_bet(self.current_bet, self.pot, self.hand_evaluator)
    #             if bet_amount > 0:
    #                 player.add_bet(bet_amount)
    #                 if self.bot_bet_update_callback:
    #                     self.bot_bet_update_callback(player.name, bet_amount)
    #         else:
    #             if self.action_callback:
    #                 bet_amount = self.action_callback("final_betting_round")
    #                 if bet_amount > 0:
    #                     if player.add_bet(bet_amount):
    #                         if self.pot_update_callback:
    #                             self.pot_update_callback(self.pot)
    #                     else:
    #                         print(f"{player.name} does not have enough funds to bet {bet_amount}.")
    #             else:
    #                 bet_amount = int(input(f"{player.name}, how much would you like to bet? Current pot is {self.pot}: "))
    #                 if bet_amount > 0:
    #                     player.set_bet(bet_amount)

    #         self.pot = sum(node.player.bet for node in self.player_nodes)
    #     if (self.pot_update_callback):
    #         self.pot_update_callback(self.pot)
        
        
    #     # Similar to initial_betting_round but with options to call, raise, or fold based on current bets.
    #     pass