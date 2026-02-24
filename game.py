
import random
from Database_Helper import Database_Helper
from Dealer import Dealer
from HandEvaluators import PokerHandEvaluator
from Player import Player, BotPlayer
from utils import show_substituted

# Linked list node for players
class PlayerNode:
    def __init__(self, player):
        self.player = player
        self.next = None
        self.prev = None

class Poker_for_GUI():
    def __init__(self, player_names,
                 action_callback=None, #Callback to request bet from GUI
                 phase_callback=None, #Callback to notify GUI of phase changes
                 pot_update_callback=None, #Updates the pot label on the GUI
                 bot_bet_update_callback=None, #Updates the bot bet label on the GUI
                 bot_fold_callback=None): #Notifies GUI that a bot has folded and shows their cards
        self.dealer = Dealer()
        self.db_helper= Database_Helper()
        self.evaluator=PokerHandEvaluator()
        
        wallet = self.db_helper.retrieve_player_wallet(player_names[0])
        override = False
        if override:
            wallet = 1000
        elif wallet is None:
            wallet = 1000 #Default
        elif wallet <= 0:
            self.db_helper.player_take_loan(player_names[0])

        # Create the user player with the correct wallet
        user_player = Player(player_names[0], action_callback=action_callback, wallet=wallet)
        bot_players = [BotPlayer(f"Bot{i}", game_type="Poker") for i in range(1, len(player_names))]
        self.players = [user_player] + bot_players
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
        
        self._betting_need_to_act = None
        self._betting_current_bet = None
        self._betting_done_callback = None
        
    def deal_initial_hands(self):
        for _ in range(2):  # Deal 2 cards to each player
            for player in self.players:
                player.request_card(self.dealer)
    
    def show_hands(self):
        for player in self.players:
            print(f"{player.name}'s hand: {show_substituted(player.hand)}")
    
    def show_only_player_hand(self):
        main_player = self.players[0]  # First player is always the human
        print(f"{main_player.name}'s hand: {show_substituted(main_player.hand)}")
        return main_player.hand
    
    def start_game(self):
        self.deal_initial_hands()
        if self.phase_callback:
            self.phase_callback('initial_hands', self.players)
        self.show_only_player_hand()
        self.betting_round(1, self.after_betting_round_1)
        #self.dealer.debug_deck()
    
    def play_again(self):
        self.dealer = Dealer()
        
        # Optionally, refresh the user's wallet from the database
        wallet = self.db_helper.retrieve_player_wallet(self.players[0].name)
        if wallet is not None:
            self.players[0].wallet = wallet
        
        # Reset all players
        for player in self.players:
            player.reset()
        
        # Reset player nodes (if you want to keep the same player objects)
        self.player_nodes = [PlayerNode(p) for p in self.players]
        n = len(self.player_nodes)
        for i in range(n):
            self.player_nodes[i].next = self.player_nodes[(i+1)%n]
            self.player_nodes[i].prev = self.player_nodes[(i-1)%n]

        self.dealt = []
        self.pot = 0
        self.minimum_bet =10
        # Start a new game
        self.start_game()
    
    def after_betting_round_1(self):
        flop=self.deal_flop()
        print(f"Flop: {show_substituted(flop)}")
        self.dealt=flop.copy()
        if self.phase_callback:
            self.phase_callback('flop', self.dealt)
        self.minimum_bet=0
        self.betting_round(2, self.after_betting_round_2)
    
    def after_betting_round_2(self):
        turn=self.deal_turn()
        print(f"Turn: {show_substituted([turn])}")
        self.dealt +=[turn]
        if self.phase_callback:
            self.phase_callback('turn', self.dealt)
        self.betting_round(3, self.after_betting_round_3)
    
    def after_betting_round_3(self):
        river=self.deal_river()
        print(f"River: {show_substituted([river])}")
        self.dealt +=[river]
        if self.phase_callback:
            self.phase_callback('river', self.dealt)
        self.betting_round(4, self.after_betting_round_4)
    
    def after_betting_round_4(self):
        print("\n--- Determining Winner ---")
        print(f"Dealt cards: {show_substituted(self.dealt)}")
        self.show_hands()
        if self.phase_callback:
            #print (self.players)
            self.phase_callback("showdown", self.players)
        self.determine_winner(self.players, self.dealt)
    
    def betting_round(self, round_number, done_callback):
        print(f"\n--- Betting Round #{round_number} ---")
        self._current_round_number = round_number  # Store the round number

        # Reset all current_bet to 0 for this round
        for node in self.player_nodes:
            node.player.current_bet = 0
        self._betting_current_bet = self.minimum_bet
        active_players = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        if len(active_players) < 2:
            print("No betting needed: only one player remains.")
            if done_callback:
                done_callback()
            return
        self._betting_need_to_act = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        self._betting_done_callback = done_callback
        self.betting_next()
        
    def get_ordered_active_nodes_after(self, raiser_node):
        result = []
        node = raiser_node.next
        while node != raiser_node:
            if not node.player.isFolded and node.player.wallet > 0:
                result.append(node)
            node = node.next
        return result

    def betting_next(self):
        # If no one left to act, finish the betting round
        if not self._betting_need_to_act:
            self.pot = sum(node.player.bet for node in self.player_nodes)
            print(f"Total pot is now: {self.pot}\n")
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
            self.bot_set_bet(player, to_call, round_number=self._current_round_number)
            #wallet_after = player.wallet
            #delta = wallet_after - wallet_before
            self.pot = sum(node.player.bet for node in self.player_nodes)
            if self.pot_update_callback:
                self.pot_update_callback(self.pot)
            bot_index = self.players.index(player) - 1  # Adjust for human player at index 0
            if self.bot_bet_update_callback:
                self.bot_bet_update_callback(bot_index, player.current_bet)
            #self.db_helper.update_player_wallet(player.name, delta)
            if player.isFolded:
                if self.bot_fold_callback:
                    self.bot_fold_callback(bot_index,hand=player.hand)
                pass  # Already removed from need_to_act
            elif player.current_bet > self._betting_current_bet:
                # Update the current bet and requeue all others except this player
                self._betting_current_bet = player.current_bet
                self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
            self.betting_next()
        else:
            # For human, call the callback and wait for GUI to resume
            if self.action_callback:
                self._last_human_node = node  # Save for resume
                self._last_human_bet = player.current_bet  # Save for resume
                self.action_callback(to_call)
            else:
                player.set_bet(to_call)
                if player.current_bet > self._betting_current_bet:
                    # Update the current bet and requeue all others except this player
                    self._betting_current_bet = player.current_bet
                    self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
                self.betting_next()
            # Wait for GUI to call resume_betting_round()
    
    def resume_betting_round(self):
        # Called after the human's bet is placed
        node = getattr(self, '_last_human_node', None)
        player = node.player if node else None
        if player and player.current_bet > self._betting_current_bet:
            self._betting_current_bet = player.current_bet
            self._betting_need_to_act = self.get_ordered_active_nodes_after(node)
        self.betting_next()
    
    def deal_flop(self):
        self.dealer.deal_self()  # Burn a card
        flop = [self.dealer.deal_card() for _ in range(3)]
        return flop
    
    def deal_turn(self):
        self.dealer.deal_self()  # Burn a card
        turn = self.dealer.deal_card()
        return turn
    
    def deal_river(self):
        self.dealer.deal_self()  # Burn a card
        river = self.dealer.deal_card()
        return river
    
    def determine_winner(self, players: list[Player], dealt):
        # Track current best rank and all players tied with that exact winning combo
        highest_rank = 0
        winning_hand = []
        winners = []
        rank_list = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

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

        def rank_val(card_or_rank):
            card_rank = self.evaluator.remove_suit_card(card_or_rank)
            return rank_list.index(card_rank)

        players = [p for p in players if not p.isFolded]
        for player in players:
            hand = player.hand
            rank, result, hand_name = self.evaluator.evaluate_hand(hand, dealt)
            result_cards = normalize_card_list(result)
            print(f"{player.name} has {hand_name}: {show_substituted(result_cards)}")

            if rank > highest_rank:
                highest_rank = rank
                winning_hand = result
                winners = [player]
                continue

            if rank != highest_rank or not winners:
                continue

            winning_hand_cards = normalize_card_list(winning_hand)
            # Precompute highest card ranks for both current winner and player
            highest_rank_winner = self.evaluator.get_highest_rank(winning_hand_cards)
            highest_rank_player = self.evaluator.get_highest_rank(result_cards)

            if rank in [2, 3]:
                # Check suits and check highest card in the hand to break ties.
                # This is a simplified tie-breaking logic and may not cover all cases.
                # Determine pair ranks for winner and player (two ranks for Two Pair)
                def get_pair_ranks(cards):
                    ranks = [self.evaluator.remove_suit_card(c) for c in cards]
                    return sorted(set(ranks), key=lambda r: rank_list.index(r), reverse=True)

                # Build kicker values from all available cards (hand + board),
                # excluding the winning pair/two-pair ranks.
                # This correctly handles shared board kickers in Texas Hold'em.
                def get_kicker_values(player_hand, board_cards, excluded_ranks, needed):
                    pool = list(player_hand) + list(board_cards)
                    values = [
                        rank_list.index(self.evaluator.remove_suit_card(c))
                        for c in pool
                        if self.evaluator.remove_suit_card(c) not in excluded_ranks
                    ]
                    values.sort(reverse=True)
                    return values[:needed]

                # Lexicographic kicker comparison (highest kicker first).
                # Returns 1 if challenger wins, -1 if leader wins, 0 if exact tie.
                def compare_kickers(challenger_vals, leader_vals):
                    for challenger_val, leader_val in zip(challenger_vals, leader_vals):
                        if challenger_val > leader_val:
                            return 1
                        if challenger_val < leader_val:
                            return -1
                    return 0

                winner_pair_ranks = get_pair_ranks(winning_hand_cards)
                player_pair_ranks = get_pair_ranks(result_cards)

                # Compare highest pair first
                if rank_list.index(player_pair_ranks[0]) > rank_list.index(winner_pair_ranks[0]):
                    winning_hand = result
                    winners = [player]
                elif rank_list.index(player_pair_ranks[0]) == rank_list.index(winner_pair_ranks[0]):
                    if len(player_pair_ranks) == 2 and len(winner_pair_ranks) == 2:
                        # Two Pair: compare second pair
                        if rank_list.index(player_pair_ranks[1]) > rank_list.index(winner_pair_ranks[1]):
                            winning_hand = result
                            winners = [player]
                        elif rank_list.index(player_pair_ranks[1]) == rank_list.index(winner_pair_ranks[1]):
                            # Two Pair: compare the single kicker from hand+board.
                            leader_kicker_vals = get_kicker_values(
                                winners[0].hand,
                                dealt,
                                set(winner_pair_ranks[:2]),
                                1,
                            )
                            player_kicker_vals = get_kicker_values(
                                hand,
                                dealt,
                                set(player_pair_ranks[:2]),
                                1,
                            )
                            kicker_cmp = compare_kickers(player_kicker_vals, leader_kicker_vals)
                            if kicker_cmp > 0:
                                winning_hand = result
                                winners = [player]
                            elif kicker_cmp == 0 and player not in winners:
                                # If the kicker is shared on the board, this remains a true tie.
                                winners.append(player)
                    else:
                        # Single Pair: compare top three kickers from hand+board.
                        leader_kicker_vals = get_kicker_values(
                            winners[0].hand,
                            dealt,
                            {winner_pair_ranks[0]},
                            3,
                        )
                        player_kicker_vals = get_kicker_values(
                            hand,
                            dealt,
                            {player_pair_ranks[0]},
                            3,
                        )
                        kicker_cmp = compare_kickers(player_kicker_vals, leader_kicker_vals)
                        if kicker_cmp > 0:
                            winning_hand = result
                            winners = [player]
                        elif kicker_cmp == 0 and player not in winners:
                            # Equal kicker vector means exact tie (including board-kicker ties).
                            winners.append(player)
            elif rank == 4:
                # Three of a kind: compare card ranks.
                # STOP GENERATING FOR KICKERS. YOU CANT HAVE TWO PLAYERS WITH THE SAME THREE OF A KIND.
                # THERE AREN'T ENOUGH CARDS IN THE DECK FOR THAT TO HAPPEN.
                if highest_rank_player > highest_rank_winner:
                    winning_hand = result
                    winners = [player]
            elif rank == 7:
                # We only need to compare the ranks of the three of a kind part of the full house.
                # The pair is unnecessary because its impossible to share three of a kinds.
                # There are only four of each rank, thus its impossible for two players to have three of a kinds of the same rank in the same hand.
                three_card_winner = rank_val(winning_hand[0])
                three_card_player = rank_val(result[0])
                if three_card_player > three_card_winner:
                    winning_hand = result
                    winners = [player]
                elif three_card_player == three_card_winner and player not in winners:
                    # Treat as tie; suits are not compared for full house
                    winners.append(player)
            elif rank in [5, 6, 8, 9]:
                # For these hand ranks, compare the highest card in the hand first.
                if highest_rank_player > highest_rank_winner:
                    winning_hand = result
                    winners = [player]
                else:
                    # If highest ranks are the same, compare next highest cards in order.
                    # If all are equal, treat as tie (no suit comparison here).
                    sorted_winner_hand = self.evaluator.sort_hand(winning_hand_cards)
                    sorted_player_hand = self.evaluator.sort_hand(result_cards)
                    decided = False
                    for w_card, p_card in zip(reversed(sorted_winner_hand), reversed(sorted_player_hand)):
                        p_val = rank_val(p_card)
                        w_val = rank_val(w_card)
                        if p_val > w_val:
                            winning_hand = result
                            winners = [player]
                            decided = True
                            break
                        if p_val < w_val:
                            decided = True
                            break
                    if not decided and highest_rank_player == highest_rank_winner and player not in winners:
                        winners.append(player)
            elif rank == 10:
                # Royal flushes tie automatically
                if player not in winners:
                    winners.append(player)
            else:
                # High Card
                if highest_rank_player > highest_rank_winner:
                    winning_hand = result
                    winners = [player]
                elif highest_rank_player == highest_rank_winner:
                    # If highest ranks are equal, compare suits of the highest card
                    winner_high_suit = self.evaluator.get_highest_suit(winning_hand_cards)
                    player_high_suit = self.evaluator.get_highest_suit(result_cards)
                    suit_rank = {"H": 4, "D": 3, "C": 2, "S": 1}
                    if suit_rank[player_high_suit] > suit_rank[winner_high_suit]:
                        winning_hand = result
                        winners = [player]

        if not winners:
            return

        winner_names = [p.name for p in winners]
        winning_hand_cards = normalize_card_list(winning_hand)
        winners_display = ", ".join(winner_names)

        if self.phase_callback:
            self.phase_callback("winner", [winners_display, winning_hand_cards, self.pot])

        if len(winners) > 1:
            print(f"Tie: {winners_display} with hand: {show_substituted(winning_hand_cards)}")
            share = self.pot // len(winners)
            remainder = self.pot % len(winners)
            for idx, winner in enumerate(winners):
                award = share + (remainder if idx == 0 else 0)
                self.award_player(winner, award)
                self.db_helper.update_player_stats(winner.name, award, True, award)
            self.db_helper.log_game("Poker", ', '.join([p.name for p in players]), winners_display, self.pot)
        else:
            winner = winners[0]
            print(f"The winner is {winner.name} with hand: {show_substituted(winning_hand_cards)}")
            self.award_player(winner, self.pot)
            self.db_helper.log_game("Poker", ', '.join([p.name for p in players]), winner.name, self.pot)
            self.db_helper.update_player_stats(winner.name, self.pot, True, self.pot)
        

    def award_player(self,player : Player,bet: int):
        player.win_bet(bet)
    
    def bot_set_bet(self, bot_player : Player, minimum_bet : int, round_number=None):
    
        #Check hand strength
        hand_strength=self.bot_assess_hand_strength(bot_player, self.dealt)
        #Determine maximum bet
        self.bot_determine_maximum_bet(bot_player,round_number=round_number)
        
        bet = minimum_bet #Default to call
        
        #---------------------------------
        #Cannot Continue Playing Scenarios
        #---------------------------------
        if bot_player.wallet <=0:
            print(f"{bot_player.name} (Bot) has no funds left to bet. Skipping turn.")
            return
        if bot_player.isFolded:
            print(f"{bot_player.name} (Bot) has already folded. Skipping turn.")
            return
        #---------------------------------
        #Check for Check Scenario
        #---------------------------------
        if (minimum_bet == 0):
            if (hand_strength<1):
                print (f"{bot_player.name} (Bot) decides to check.")
                return
            else:
                bet = random.randint(10, min(50, bot_player.wallet))
                print (f"{bot_player.name} (Bot) decides to bet {bet} instead of checking.")
                return
        #---------------------------------
        #All-in Scenario
        #---------------------------------
        elif (minimum_bet > bot_player.wallet):
            minimum_bet = bot_player.wallet
            #Pair or worse, don't do it.
            if (hand_strength<=1):
                bot_player.isFolded=True
                print(f"{bot_player.name} (Bot) decides to fold as it does not want to\n"+
                      f"all-in on the bet of {minimum_bet}.")
            #Three of a kind or better, go for it.
            elif (hand_strength>1):
                print (f"{bot_player.name} (Bot) is going all-in with {minimum_bet}.")
                bot_player.add_bet(minimum_bet)
            return
        #---------------------------------
        #Call/Raise Scenario
        #---------------------------------
        else:
            maximum_bet = bot_player.maximum_bet
            print(f"{bot_player.name} (Bot) has a maximum willingness to bet of {maximum_bet} based on its hand strength and risk tolerance.")
            #If the requirement to call, is greater than the maximum_bet minus
            #the existing current_bet (already placed bet)
            if (minimum_bet > maximum_bet-bot_player.current_bet):
                #If the requirement to call is not 1.5 times more than the remaining allowable bet
                if (minimum_bet*1.5 <= maximum_bet-bot_player.current_bet):
                    #Make the bet.
                    if (hand_strength<=1):
                        bot_player.isFolded=True
                        print(
                            f"{bot_player.name} (Bot) decides to fold as the minimum bet {minimum_bet}\n"
                            f"+ existing bet of {bot_player.current_bet} exceeds its maximum willingness to bet {maximum_bet}."
                        )
                        return
                    #Three of a kind or better, go for it.
                    elif (hand_strength>1):
                        print (f"{bot_player.name} (Bot) has called. Remaining funds: {bot_player.wallet}")
                        bet=minimum_bet
                else:
                    # Bluffing chance
                    randomNumber=random.random()
                    print(f"Random number for bluff decision: {randomNumber}")
                    if (randomNumber>0.9):
                        print(f"{bot_player.name} (Bot) thinks you are bluffing and matches your bet\n" +
                                f"despite the odds.")
                        bet=minimum_bet
                    else:
                        print(
                            f"{bot_player.name} (Bot) decides to fold as the minimum bet {minimum_bet}\n"
                            f"+ existing bet of {bot_player.current_bet} exceeds its maximum willingness to bet {maximum_bet}."
                        )
                        bot_player.isFolded=True
                        return
            else:
                if (minimum_bet > maximum_bet):
                    print(
                        f"{bot_player.name} (Bot) decides to fold as the minimum bet {minimum_bet}\n"
                        f"+ existing bet of {bot_player.current_bet} exceeds its maximum willingness to bet {maximum_bet}."
                    )
                    bot_player.isFolded=True
                    return
                
                if (bot_player.risk_tolerance=="low" and bot_player.current_bet >= maximum_bet*0.5):
                    #bet = minimum_bet
                    pass
                elif (bot_player.risk_tolerance=="medium" and bot_player.current_bet >= maximum_bet*0.7):
                    bet = random.randint(minimum_bet, int(maximum_bet*0.7))
                else:
                    bet = random.randint(minimum_bet, min(maximum_bet, bot_player.wallet))
        
        if bet is not None:
            bot_player.add_bet(bet)
            if (bet == minimum_bet):
                print (f"{bot_player.name} (Bot) has called. Remaining funds: {bot_player.wallet}")
            else:
                print(f"{bot_player.name} (Bot) has raised their bet by {bet}. Remaining funds: {bot_player.wallet}")
        
    def bot_determine_maximum_bet(self, bot_player : BotPlayer, round_number=None):
        # Assess using the bot player object, not its hand list
        bot_player.maximum_bet=int(100*self.bot_assess_risk(bot_player) + 100* self.bot_assess_hand_strength(bot_player, self.dealt))
        # Risk | Hand Strength Category         | Strength | Calc                        | max_bet
        # -----|-------------------------------|----------|-----------------------------|---------
        # 0.2  | High Card                     | 0.5      | 100*0.2 + 100*0.5           | 70
        # 0.2  | Pair or Two Pair              | 1        | 100*0.2 + 100*1             | 120
        # 0.2  | Three of a Kind to Straight   | 1.5      | 100*0.2 + 100*1.5           | 170
        # 0.2  | Full House or better          | 3.0      | 100*0.2 + 100*3.0           | 320
        # 0.5  | High Card                     | 0.5      | 100*0.5 + 100*0.5           | 100
        # 0.5  | Pair or Two Pair              | 1        | 100*0.5 + 100*1             | 150
        # 0.5  | Three of a Kind to Straight   | 1.5      | 100*0.5 + 100*1.5           | 200
        # 0.5  | Full House or better          | 3.0      | 100*0.5 + 100*3.0           | 350
        # 1    | High Card                     | 0.5      | 100*1 + 100*0.5             | 150
        # 1    | Pair or Two Pair              | 1        | 100*1 + 100*1               | 200
        # 1    | Three of a Kind to Straight   | 1.5      | 100*1 + 100*1.5             | 250
        # 1    | Full House or better          | 3.0      | 100*1 + 100*3.0             | 400
    
    def bot_assess_risk(self, bot_player : Player):
        if bot_player.risk_tolerance == "low":
            return 0.2
        elif bot_player.risk_tolerance == "medium":
            return 0.5
        else:  # high risk tolerance
            return 1
    
    
    def bot_assess_hand_strength(self, bot_player : Player, dealt):
        rank, result, name = self.evaluator.evaluate_hand(bot_player.hand, dealt)
        print (f"Bot hand evaluation: Rank {rank}, Hand: {show_substituted(result)}")
        print (f"{bot_player.name} (Bot) assesses its hand as a {name}.")
        if rank >= 7:  # Full House or better
            return 3.0
        elif rank >= 4:  # Three of a Kind to Straight
            return 1.5
        elif rank >= 2:  # Pair to Two Pair
            return 1
        else:  # High Card
            return 0.5
    
    
    
def game_start():
    print("Starting Poker Game...")
    print("Please enter your name:")
    override=True
    if override:
        player_name="Dev"
    else:
        player_name = input()
    print("Welcome, " + player_name + "!")
    print("How many players (including you) will be playing? (2-6)")
    num_players_input = input()
    try:
        num_players = int(num_players_input)
        if num_players < 2 or num_players > 6:
            print("Invalid number of players. Defaulting to 2 players.")
            num_players = 2
    except ValueError:
        print("Invalid input. Defaulting to 2 players.")
        num_players = 2

    poker_game = Poker_for_GUI([player_name] + [f"Bot{i}" for i in range(1, num_players)])
    poker_game.start_game()

if __name__ == "__main__":
    game_start()