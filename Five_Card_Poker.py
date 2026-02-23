
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
        self.minimum_bet=10
        
        
        self.action_callback = action_callback
        self.phase_callback = phase_callback
        self.pot_update_callback = pot_update_callback
        self.bot_bet_update_callback = bot_bet_update_callback
        self.bot_fold_callback = bot_fold_callback
        
        self._betting_need_to_act = None
        self._betting_current_bet = None
        self._betting_done_callback = None
        self._waiting_for_discard = False

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
        if (self.phase_callback):
            self.phase_callback("update_initial_hands", {"players": self.players})
            
            
    def discard_phase(self):
        for node in self.player_nodes:
            player = node.player

            if player.isBot:
                continue
                num_to_discard = 0
                if hasattr(player, "decide_discard"):
                    try:
                        num_to_discard = player.decide_discard(self.evaluator)
                    except Exception:
                        num_to_discard = 0
                if num_to_discard > 0 and hasattr(player, "choose_discard_indices"):
                    try:
                        indices_to_discard = player.choose_discard_indices(num_to_discard)
                    except Exception:
                        indices_to_discard = []
                    for index in sorted(indices_to_discard[:3], reverse=True):
                        player.discard_card(self.dealer, index)
                continue

            if self.action_callback:
                indices_to_discard = self.action_callback(
                    "cards_to_discard_phase",
                    {
                        "player_name": player.name,
                        "max_to_discard": 3,
                    },
                )
                #print (f"Player {player.name} wants to discard indices: {indices_to_discard}")
                if indices_to_discard is None:
                    self._waiting_for_discard = True
                    return
                safe_indices = []
                for idx in indices_to_discard[:3]:
                    try:
                        parsed_idx = int(idx)
                    except Exception:
                        continue
                    if 0 <= parsed_idx < len(player.hand):
                        safe_indices.append(parsed_idx)
                for index in sorted(set(safe_indices), reverse=True):
                    player.discard_card(self.dealer, index)
            else:
                num_to_discard = int(input(f"{player.name}, how many cards would you like to discard? (0-3): "))
                if num_to_discard > 0:
                    indices_to_discard = input(f"Which card indices would you like to discard? (0-{len(player.hand)-1}, separate by commas): ")
                    indices_to_discard = [int(idx.strip()) for idx in indices_to_discard.split(",")]
                    for index in sorted(indices_to_discard[:num_to_discard], reverse=True):
                        player.discard_card(self.dealer, index)

        self._waiting_for_discard = False
        self.deal_new_cards()

    def resume_discard_phase(self):
        if self._waiting_for_discard:
            self.discard_phase()
        
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
            self.phase_callback("update_hands", {"players": self.players})
            #self.action_callback("final_betting_round")
            
        self.betting_round(minimum_bet=0, round_name="final_betting_round")
    
    def get_ordered_active_nodes_after(self, raiser_node):
        result = []
        node = raiser_node.next
        while node != raiser_node:
            if not node.player.isFolded and node.player.wallet > 0:
                result.append(node)
            node = node.next
        return result
    
    def bot_set_bet(self, player, to_call, round_number):
        if player.isFolded or player.wallet <= 0:
            return

        required_to_call = max(0, int(to_call))
        if required_to_call == 0:
            return

        wager = min(required_to_call, player.wallet)
        player.add_to_bet(wager)
    
    def betting_round(self, minimum_bet=10, round_name="betting_round"):
        print(f"DEBUG: Starting betting round: {round_name} with minimum bet: {minimum_bet}")
        # Set round_number based on round_name if not already set
        if round_name == "initial_betting_round":
            self.current_round_number = 1
        elif round_name == "final_betting_round":
            self.current_round_number = 2

        # Round-local bet tracking must reset each round so players act again
        # in the final betting phase after discard/draw.
        for node in self.player_nodes:
            node.player.current_bet = 0

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
        self.betting_run()

    def betting_run(self):
        # Iterative version of betting flow to avoid recursive stack frames
        while True:
            # Finish betting round if no one left to act
            if not self._betting_need_to_act:
                self.pot = sum(node.player.bet for node in self.player_nodes)
                if self._betting_done_callback:
                    cb = self._betting_done_callback
                    self._betting_done_callback = None
                    cb()
                break

            node = self._betting_need_to_act.pop(0)
            player = node.player

            # Skip folded or broke players
            if player.isFolded or player.wallet <= 0:
                continue

            # If already matched the current bet, skip
            if self._betting_current_bet > 0 and player.current_bet == self._betting_current_bet:
                continue

            to_call = max(0, self._betting_current_bet - player.current_bet)
            print(f"{player.name}'s turn. Current bet to call: {to_call}. Wallet: {player.wallet}")

            if player.isBot:
                self.bot_set_bet(player, to_call, round_number=self.current_round_number)
                bot_index = self.players.index(player) - 1  # human is index 0

                if player.isFolded:
                    if self.bot_fold_callback:
                        self.bot_fold_callback(bot_index, hand=player.hand)
                    continue

                # Update pot and GUI callbacks
                self.pot = sum(node.player.bet for node in self.player_nodes)
                if self.pot_update_callback:
                    self.pot_update_callback(self.pot)
                if self.bot_bet_update_callback:
                    self.bot_bet_update_callback(bot_index, player.current_bet)

                # Handle raises: requeue all others after this player
                if player.current_bet > self._betting_current_bet:
                    self._betting_current_bet = player.current_bet
                    self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
                    # Loop continues so everyone acts again
                    continue
            else:
                # Human: use callback or immediate set_bet
                if self.action_callback:
                    self._last_human_node = node
                    self._last_human_bet = player.current_bet
                    self.action_callback(
                        "to_call",
                        {
                            "to_call": to_call,
                            "player_name": player.name,
                            "round_number": self.current_round_number,
                            "round_name": (
                                "initial_betting_round"
                                if self.current_round_number == 1
                                else "final_betting_round"
                            ),
                        },
                    )
                    # Wait for external resume; exit loop
                    break
                else:
                    player.set_bet(to_call)
                    if player.current_bet > self._betting_current_bet:
                        self._betting_current_bet = player.current_bet
                        self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
                        continue
            # If no raise and player acted, continue to next in queue
    
    # def betting_next(self): #For GUI
    #     # If no one left to act, finish the betting round
    #     if not self._betting_need_to_act:
    #         self.pot = sum(node.player.bet for node in self.player_nodes)
    #         #print(f"Total pot is now: {self.pot}\n")
    #         if self._betting_done_callback:
    #             self._betting_done_callback()
    #         return

    #     node = self._betting_need_to_act.pop(0)
    #     player = node.player
    #     if player.isFolded or player.wallet <= 0:
    #         self.betting_next()
    #         return
    #     if self._betting_current_bet > 0 and player.current_bet == self._betting_current_bet:
    #         self.betting_next()
    #         return

    #     to_call = max(0, self._betting_current_bet - player.current_bet)
    #     print(f"{player.name}'s turn. Current bet to call: {to_call}. Wallet: {player.wallet}")

    #     #wallet_before = player.wallet
    #     if player.isBot:
    #         self.bot_set_bet(player, to_call, round_number=self.current_round_number)
    #         bot_index = self.players.index(player) - 1  # Adjust for human player at index 0
    #         # Check to see if the bot folds before updating wallet/pot/callbacks
    #         if player.isFolded:
    #             if self.bot_fold_callback:
    #                 self.bot_fold_callback(bot_index, hand=player.hand)
    #             # Skip wallet/pot/bet updates for folded bot
    #             self.betting_next()
    #             return
    #         #wallet_after = player.wallet
    #         #delta = wallet_after - wallet_before
    #         self.pot = sum(node.player.bet for node in self.player_nodes)
    #         if self.pot_update_callback:
    #             self.pot_update_callback(self.pot)
    #         if self.bot_bet_update_callback:
    #             self.bot_bet_update_callback(bot_index, player.current_bet)
    #         #self.db_helper.update_player_wallet(player.name, delta)
    #         if player.current_bet > self._betting_current_bet:
    #             # Update the current bet and requeue all others except this player
    #             self._betting_current_bet = player.current_bet
    #             self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
    #         self.betting_next()
    #     else:
    #         # For human, call the callback and wait for GUI to resume
    #         if self.action_callback:
    #             self._last_human_node = node  # Save for resume
    #             self._last_human_bet = player.current_bet  # Save for resume
    #             self.action_callback(
    #                 "to_call",
    #                 {
    #                     "to_call": to_call,
    #                     "player_name": player.name,
    #                 },
    #             )
    #         else:
    #             player.set_bet(to_call)
    #             if player.current_bet > self._betting_current_bet:
    #                 # Update the current bet and requeue all others except this player
    #                 self._betting_current_bet = player.current_bet
    #                 self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
    #             self.betting_next()
    #         # Wait for GUI to call resume_betting_round()
    def showdown(self):
        print(f"The final pot total is: {self.pot}\n")
        self.show_hands()
        self.determine_winner()
    
    def award_player(self,player : Player,bet: int):
        player.win_bet(bet)
    
    def determine_winner(self):
        # Track current best rank and all players tied with that exact winning combo
        highest_rank = 0
        winning_hand = []
        winners = []  # list[Player]

        def normalize_card_list(value):
            cards = []

            def collect(item):
                if isinstance(item, str):
                    cards.append(item)
                elif isinstance(item, (list, tuple)):
                    for nested_item in item:
                        collect(nested_item)

            collect(value)
            return cards

        players = [p for p in self.players if not p.isFolded]
        # Guard: if any active player has an empty hand, determining a winner will fail
        # if any(len(p.hand) == 0 for p in players):
        #     print("Warning: One or more active players have empty hands. Deal or set hands before showdown.")
        #     if self.phase_callback:
        #         self.phase_callback("winner", {"winner_names": [], "winning_hand": [], "pot": self.pot})
        #     return
        for player in players:
            hand = player.hand
            print (hand)
            rank, result, hand_name = self.evaluator.evaluate_hand(hand, [])
            result_cards = normalize_card_list(result)
            print(f"{player.name} has {hand_name}: {show_substituted(result_cards)}")
            if rank > highest_rank:
                highest_rank = rank
                winning_hand = result
                winners = [player]
            if rank == highest_rank and winners:
                winning_hand_cards = normalize_card_list(winning_hand)
                # Precompute highest card ranks for both current winner and player
                highest_rank_winner = self.evaluator.get_highest_rank(winning_hand_cards)
                highest_rank_player = self.evaluator.get_highest_rank(result_cards)
                #Check suits and check highest card in the hand to break ties. 
                # This is a simplified tie-breaking logic and may not cover all cases.
                if (rank in [2, 3]): #Pair, Two Pair
                    # Determine pair ranks for winner and player (two ranks for Two Pair)
                    from utils import rank as rank_list
                    def get_pair_ranks(cards):
                        ranks = [self.evaluator.remove_suit_card(c) for c in cards]
                        unique = sorted(set(ranks), key=lambda r: rank_list.index(r), reverse=True)
                        return unique
                    winner_pair_ranks = get_pair_ranks(winning_hand_cards)
                    player_pair_ranks = get_pair_ranks(result_cards)

                    # Compare highest pair first
                    def rank_val(r):
                        return rank_list.index(r)
                    if rank_val(player_pair_ranks[0]) > rank_val(winner_pair_ranks[0]):
                        winning_hand = result
                        winners = [player]
                    elif rank_val(player_pair_ranks[0]) == rank_val(winner_pair_ranks[0]):
                        if len(player_pair_ranks) == 2 and len(winner_pair_ranks) == 2:
                            # Two Pair: compare second pair
                            if rank_val(player_pair_ranks[1]) > rank_val(winner_pair_ranks[1]):
                                winning_hand = result
                                winners = [player]
                            elif rank_val(player_pair_ranks[1]) == rank_val(winner_pair_ranks[1]):
                                # Compare kickers (hand minus the pair cards)
                                leader_kickers = [c for c in winners[0].hand if c not in winning_hand]
                                player_kickers = [c for c in hand if c not in result]
                                winner_high_card = self.evaluator.get_highest_rank(leader_kickers)
                                player_high_card = self.evaluator.get_highest_rank(player_kickers)
                                if player_high_card > winner_high_card:
                                    winning_hand = result
                                    winners = [player]
                                elif player_high_card == winner_high_card:
                                    # Two Pair: if kickers equal, it's a tie (no suit precedence)
                                    if player not in winners:
                                        winners.append(player)
                        else:
                            # Single Pair: compare kickers after equal pair rank
                            leader_kickers = [c for c in winners[0].hand if c not in winning_hand]
                            player_kickers = [c for c in hand if c not in result]
                            winner_high_card = self.evaluator.get_highest_rank(leader_kickers)
                            player_high_card = self.evaluator.get_highest_rank(player_kickers)
                            if player_high_card > winner_high_card:
                                winning_hand = result
                                winners = [player]
                            elif player_high_card == winner_high_card:
                                # Only pairs use suit precedence
                                winner_high_suit = self.evaluator.get_highest_suit(winning_hand_cards)
                                player_high_suit = self.evaluator.get_highest_suit(result_cards)
                                suit_rank = {"H": 4, "D": 3, "C": 2, "S": 1}
                                if suit_rank[player_high_suit] > suit_rank[winner_high_suit]:
                                    winning_hand = result
                                    winners = [player]
                elif (rank == 4):
                    # Three of a kind: compare card ranks.
                    #STOP GENERATING FOR KICKERS. YOU CANT HAVE TWO PLAYERS WITH THE SAME THREE OF A KIND.
                    #THERE AREN'T ENOUGH CARDS IN THE DECK FOR THAT TO HAPPEN.
                    if highest_rank_player > highest_rank_winner:
                        winning_hand = result
                        winners = [player]
                    
                elif rank == 7: #Full House
                    #We only need to compare the ranks of the three of a kind part of the full house.
                    #The pair is unnecessary because its impossible to share three of a kinds.
                    #There are only four of each rank, thus its impossible for two players to have three of a kinds of the same rank in the same hand.
                    three_card_winner = self.evaluator.remove_suit_card(winning_hand[0])
                    three_card_player = self.evaluator.remove_suit_card(result[0])
                    if three_card_player > three_card_winner:
                        winning_hand = result
                        winners = [player]
                    elif three_card_player == three_card_winner:
                        # Treat as tie; suits are not compared for full house
                        if player not in winners:
                            winners.append(player)
                elif rank in [5, 6, 8, 9]: #Straight, Flush, Four of a Kind, Straight Flush
                    #For these hand ranks, we can compare the highest card in the hand first, then suits if needed.
                    if highest_rank_player > highest_rank_winner:
                        winning_hand = result
                        winners = [player]
                    else:
                        #If highest ranks are the same, we can compare the next highest card, 
                        #and so on until we find a difference or run out of cards to compare. 
                        #If we run out of cards to compare, then its a tie.
                        sorted_winner_hand = self.evaluator.sort_hand(winning_hand_cards)
                        sorted_player_hand = self.evaluator.sort_hand(result_cards)
                        decided = False
                        for w_card, p_card in zip(reversed(sorted_winner_hand), reversed(sorted_player_hand)):
                            if self.evaluator.remove_suit_card(p_card) > self.evaluator.remove_suit_card(w_card):
                                winning_hand = result
                                winners = [player]
                                decided = True
                                break
                        # If ranks compare equal across all cards, it's a tie (no suit comparison here)
                        if not decided and highest_rank_player == highest_rank_winner:
                            if player not in winners:
                                winners.append(player)
                elif rank == 10: #Royal Flush
                    # Royal flushes tie automatically
                    if player not in winners:
                        winners.append(player)
                else: #High Card
                    if highest_rank_player > highest_rank_winner:
                        winning_hand = result
                        winners = [player]
                    elif highest_rank_player == highest_rank_winner:
                         # If high card ranks are equal, compare suits of the high card
                        winner_high_suit = self.evaluator.get_highest_suit(winning_hand_cards)
                        player_high_suit = self.evaluator.get_highest_suit(result_cards)
                        suit_rank = {"H": 4, "D": 3, "C": 2, "S": 1}
                        if suit_rank[player_high_suit] > suit_rank[winner_high_suit]:
                            winning_hand = result
                            winners = [player]
        # # Announce winners and split pot if tied
        # if not winners:
        #     print("No winner could be determined. Ensure hands are set correctly.")
        #     if self.phase_callback:
        #         self.phase_callback("winner", {"winner_names": [], "winning_hand": [], "pot": self.pot})
        #     return
        
        winner_names = [p.name for p in winners]
        winning_hand_cards = normalize_card_list(winning_hand)
        if self.phase_callback:
            self.phase_callback(
                "winner",
                {
                    "winner_names": winner_names,
                    "winning_hand": winning_hand_cards,
                    "pot": self.pot,
                },
            )
        if len(winner_names) > 1:
            print(f"Tie: {', '.join(winner_names)} with hand: {show_substituted(winning_hand_cards)}")
            share = self.pot // len(winners)
            remainder = self.pot % len(winners)
            for idx, w in enumerate(winners):
                award = share + (remainder if idx == 0 else 0)
                self.award_player(w, award)
                self.db_helper.update_player_stats(w.name, award, True, award)
            self.db_helper.log_game("Poker", ', '.join([p.name for p in players]), ', '.join(winner_names), self.pot)
        else:
            leader = winners[0]
            print(f"The winner is {leader.name} with hand: {show_substituted(winning_hand_cards)}")
            self.award_player(leader, self.pot)
            self.db_helper.log_game("Poker", ', '.join([p.name for p in players]), leader.name, self.pot)
            self.db_helper.update_player_stats(leader.name, self.pot, True, self.pot)
    
    
    
    def set_debug_hands(self, hands_by_name: dict):
        for p in self.players:
            if p.name in hands_by_name:
                p.hand = list(hands_by_name[p.name])
                p.isFolded = False
                if not hasattr(p, 'current_bet'):
                    p.current_bet = 0
        # Reset pot to avoid stale values from previous rounds
        self.pot = sum(getattr(p, 'current_bet', 0) for p in self.players)
        
    def debug_deal_hands(self):
        # Debug function to deal specific hands for testing
        main_player = self.get_main_player()
        main_player.hand = ["9C", "10C", "JC", "QC", "KC"]  # Royal Flush
        self.player_nodes[1].player.hand = ["9D", "10D", "JD", "QD", "KD"]  # Straight Flush
        self.player_nodes[2].player.hand = ["2C", "2D", "2H", "5S", "7D"]  # Three of a Kind
    
    def debug_start_game(self):
        self.debug_deal_hands()
        self.betting_round(minimum_bet=self.minimum_bet, round_name="initial_betting_round")
    
    def start_game(self):
        # self.debug_start_game()
        # return
        
        #Five Card Poker.
        #Get initial buy in bets.
        #Deal cards in a circle, one at a time, until everyone has 5 cards.
        
        self.deal_initial_hands()
        
        self.show_only_player_hand()
        
        #self.show_hands()
        self.betting_round(minimum_bet=self.minimum_bet, round_name="initial_betting_round")
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
#     game.set_debug_hands({
#     "You": ["AH","KH","QH","JH","10H"],
#     "Bot1": ["9C","9D","9S","2H","3D"],
#     "Bot2": ["AS","AD","AC","KS","QD"],
# })
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