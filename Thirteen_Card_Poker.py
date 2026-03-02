
from Database_Helper import Database_Helper
from Dealer import Dealer
from HandEvaluators import PokerHandEvaluator
from Player import BotPlayer, Player
from utils import show_substituted
from itertools import combinations
from collections import Counter



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

class ThirteenCardPoker():
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
        
        if len(player_names) < 2:
            raise ValueError("At least two players are required to play.")
        elif len(player_names) > 4:
            raise ValueError("A maximum of four players are supported.")
        
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
        self.rank_list = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

        # Debug/testing override:
        # When True, CLI user split prompt is skipped and user hand is auto-configured.
        self.debug_skip_user_cli_arrangement = True

    def get_main_player_node(self):
        # Helper to retrieve the non-bot (human) player's node
        return next(node for node in self.player_nodes if not node.player.isBot)

    def get_main_player(self):
        # Helper to retrieve the non-bot (human) player
        return self.get_main_player_node().player

    def deal_initial_hands(self):
        # Deal cards in a circle, one at a time, until everyone has 13 cards.
        #In thirteen card poker, each player has three hands: 
        #front (3 cards), middle (5 cards), back (5 cards)
        for _ in range(13):
            for node in self.player_nodes:
                card = self.dealer.deal_card()
                node.player.hand.append(card)
        if (self.phase_callback):
            self.phase_callback("update_initial_hands", {"players": self.players})

    def rank_value(self, card):
        return self.rank_list.index(card[:-1])

    def score_front_three(self, hand_three):
        # Front hand is 3 cards: High Card, Pair, or Trips.
        # We map categories onto the same rough scale as 5-card ranks:
        #   High Card -> 1, Pair -> 2, Trips -> 4
        rank_values = sorted([self.rank_value(card) for card in hand_three], reverse=True)
        counts = Counter(rank_values)
        grouped = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)

        max_count = max(counts.values())
        if max_count == 3:
            category = 4
        elif max_count == 2:
            category = 2
        else:
            category = 1

        # Tie-break tuple: grouped ranks first (by count and strength), then raw desc ranks.
        grouped_ranks = tuple(rank for rank, _ in grouped)
        return (category, grouped_ranks, tuple(rank_values))

    def score_five(self, hand_five):
        # Category from evaluator + stable rank-vector fallback for ordering candidates.
        rank_value, _, _ = self.evaluator.evaluate_hand(hand_five, [])
        rank_values = tuple(sorted([self.rank_value(card) for card in hand_five], reverse=True))
        return (rank_value, rank_values)

    def score_for_order(self, hand):
        if len(hand) == 3:
            return self.score_front_three(hand)
        if len(hand) == 5:
            return self.score_five(hand)
        raise ValueError("Hand length for scoring must be 3 or 5.")

    def get_hand_name(self, hand):
        if len(hand) == 3:
            category = self.score_front_three(hand)[0]
            if category == 4:
                return "Three of a Kind"
            if category == 2:
                return "Pair"
            return "High Card"
        if len(hand) == 5:
            _, _, hand_name = self.evaluator.evaluate_hand(hand, [])
            return hand_name
        return "Unknown"

    def validate_3_5_5_split(self, source_hand, front_hand, middle_hand, back_hand, enforce_strength_order=True):
        # Enforce shape: 3, 5, 5
        if len(front_hand) != 3 or len(middle_hand) != 5 or len(back_hand) != 5:
            return False, "Invalid split size. Required exactly 3, 5, and 5 cards."

        # Enforce card usage: every source card must be used exactly once.
        source_counter = Counter(source_hand)
        split_counter = Counter(front_hand + middle_hand + back_hand)
        if source_counter != split_counter:
            return False, "Split must use exactly the same 13 cards with no duplicates or omissions."

        # Enforce strength ordering only when requested (bots).
        if enforce_strength_order:
            front_score = self.score_for_order(front_hand)
            middle_score = self.score_for_order(middle_hand)
            back_score = self.score_for_order(back_hand)
            if not (front_score <= middle_score <= back_score):
                return False, "Invalid ordering. Hands must be weak->strong->strongest (3,5,5)."

        return True, "ok"

    def auto_arrange_best_split(self, source_hand):
        if len(source_hand) != 13:
            raise ValueError("Auto-arrange requires exactly 13 cards.")

        cards = list(source_hand)
        all_indices = tuple(range(13))
        best_split = None
        best_metric = None

        # Brute-force search over all legal 3-5-5 partitions.
        # 13C3 * 10C5 = 72,072 candidate arrangements.
        for front_indices in combinations(all_indices, 3):
            front_index_set = set(front_indices)
            front_hand = [cards[index] for index in front_indices]
            front_score = self.score_for_order(front_hand)

            remaining_indices = [index for index in all_indices if index not in front_index_set]
            for middle_indices in combinations(remaining_indices, 5):
                middle_index_set = set(middle_indices)
                middle_hand = [cards[index] for index in middle_indices]
                back_hand = [cards[index] for index in remaining_indices if index not in middle_index_set]

                middle_score = self.score_for_order(middle_hand)
                back_score = self.score_for_order(back_hand)

                if not (front_score <= middle_score <= back_score):
                    continue

                # Optimize for strongest back, then middle, then front.
                metric = (back_score, middle_score, front_score)
                if best_metric is None or metric > best_metric:
                    best_metric = metric
                    best_split = {
                        "front": front_hand,
                        "middle": middle_hand,
                        "back": back_hand,
                    }

        if best_split is None:
            raise ValueError("No valid 3-5-5 ordering found for the provided hand.")

        return best_split

    def auto_arrange_player_hand(self, player):
        split = self.auto_arrange_best_split(player.hand)
        is_valid, message = self.validate_3_5_5_split(
            player.hand,
            split["front"],
            split["middle"],
            split["back"],
            enforce_strength_order=True,
        )
        if not is_valid:
            raise ValueError(f"Auto-arranged split failed validation for {player.name}: {message}")

        # Store on player object for later CLI/game use.
        player.front_hand = split["front"]
        player.middle_hand = split["middle"]
        player.back_hand = split["back"]
        return split

    def assign_user_split_no_order(self, player):
        # Human player exception: only enforce 3/5/5 card split usage, not weak->strong ordering.
        front = list(player.hand[:3])
        middle = list(player.hand[3:8])
        back = list(player.hand[8:13])
        is_valid, message = self.validate_3_5_5_split(
            player.hand,
            front,
            middle,
            back,
            enforce_strength_order=False,
        )
        if not is_valid:
            raise ValueError(f"User split failed validation for {player.name}: {message}")

        player.front_hand = front
        player.middle_hand = middle
        player.back_hand = back
        return {"front": front, "middle": middle, "back": back}

    def _parse_indices_input(self, raw_text, expected_count, allowed_indices):
        tokens = raw_text.replace(",", " ").split()
        if len(tokens) != expected_count:
            raise ValueError(f"Please enter exactly {expected_count} indices.")
        try:
            parsed = [int(token) for token in tokens]
        except ValueError:
            raise ValueError("Indices must be integers.")
        if len(set(parsed)) != expected_count:
            raise ValueError("Duplicate indices are not allowed.")
        invalid = [index for index in parsed if index not in allowed_indices]
        if invalid:
            raise ValueError(f"Invalid index/indices: {invalid}")
        return parsed

    def _print_indexed_hand(self, cards, allowed_indices=None):
        allowed = set(allowed_indices) if allowed_indices is not None else set(range(len(cards)))
        # Display order for readability only (does NOT mutate the real hand order):
        # singles first, then pairs, trips, and quads; grouped by rank.
        rank_counts = Counter(card[:-1] for card in cards)
        ordered_indices = sorted(
            [idx for idx in range(len(cards)) if idx in allowed],
            key=lambda idx: (
                rank_counts[cards[idx][:-1]],   # 1, 2, 3, 4
                self.rank_value(cards[idx]),    # rank order within each group
                cards[idx][-1],                 # stable suit tiebreak for display
            ),
        )
        if not ordered_indices:
            print("Cards: (none)")
            print("Index: (none)")
            return

        card_labels = [show_substituted([cards[idx]])[0] for idx in ordered_indices]

        # Column width ensures card and index rows stay visually aligned.
        col_widths = []
        for idx, card_text in zip(ordered_indices, card_labels):
            col_widths.append(max(len(card_text), len(str(idx))))

        cards_row = "Cards: " + " ".join(
            card_text.rjust(width)
            for card_text, width in zip(card_labels, col_widths)
        )
        index_row = "Index: " + " ".join(
            str(idx).rjust(width)
            for idx, width in zip(ordered_indices, col_widths)
        )

        print(cards_row)
        print(index_row)

    def _sort_hand_for_display(self, hand):
        # Display-only ordering:
        # 1) singletons first, repeated ranks later
        # 2) lowest rank -> highest rank within each section
        rank_counts = Counter(card[:-1] for card in hand)
        return sorted(
            list(hand),
            key=lambda card: (
                0 if rank_counts[card[:-1]] == 1 else 1,
                self.rank_value(card),
                card[-1],
            ),
        )

    def _resolve_player_split(self, player):
        if player.isBot:
            split = self.auto_arrange_player_hand(player)
            mode = "bot auto"
        else:
            if self.debug_skip_user_cli_arrangement:
                split = self.auto_arrange_best_split(player.hand)
                player.front_hand = split["front"]
                player.middle_hand = split["middle"]
                player.back_hand = split["back"]
                mode = "user debug auto"
            elif self.action_callback:
                split = self.assign_user_split_no_order(player)
                mode = "user default"
            else:
                split = self.prompt_user_split_cli(player)
                mode = "user manual"
        return split, mode

    def configure_player_splits(self, print_output=False):
        if print_output:
            print("\n--- Configured 3-5-5 hands ---")

        for player in self.players:
            split, mode = self._resolve_player_split(player)

            if print_output:
                front_name = self.get_hand_name(split["front"])
                middle_name = self.get_hand_name(split["middle"])
                back_name = self.get_hand_name(split["back"])
                front_display = show_substituted(self._sort_hand_for_display(split["front"]))
                middle_display = show_substituted(self._sort_hand_for_display(split["middle"]))
                back_display = show_substituted(self._sort_hand_for_display(split["back"]))
                print(
                    f"{player.name} [{mode}]: \n"
                    f"Front({front_name})={front_display} | "
                    f"Middle({middle_name})={middle_display} | "
                    f"Back({back_name})={back_display}"
                )


    def prompt_user_split_cli(self, player):
        # CLI prompt flow for the human player. Ordering is intentionally NOT enforced.
        cards = list(player.hand)
        all_indices = set(range(len(cards)))

        while True:
            print("\nArrange your 13 cards into Front(3), Middle(5), Back(5).")
            print("Your card indices:")
            self._print_indexed_hand(cards)

            try:
                front_input = input("Enter 3 indices for Front hand (e.g. 0 4 7): ")
                front_indices = self._parse_indices_input(front_input, 3, all_indices)

                remaining_after_front = all_indices - set(front_indices)
                print("Remaining indices for Middle/Back:")
                self._print_indexed_hand(cards, remaining_after_front)

                middle_input = input("Enter 5 indices for Middle hand: ")
                middle_indices = self._parse_indices_input(middle_input, 5, remaining_after_front)

                back_indices = sorted(list(remaining_after_front - set(middle_indices)))
                front = [cards[i] for i in sorted(front_indices)]
                middle = [cards[i] for i in sorted(middle_indices)]
                back = [cards[i] for i in back_indices]

                is_valid, message = self.validate_3_5_5_split(
                    cards,
                    front,
                    middle,
                    back,
                    enforce_strength_order=False,
                )
                if not is_valid:
                    print(f"Invalid split: {message}")
                    continue

                player.front_hand = front
                player.middle_hand = middle
                player.back_hand = back
                return {"front": front, "middle": middle, "back": back}
            except Exception as exc:
                print(f"Input error: {exc}")
                print("Please try again.")
    
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

    def _run_post_initial_round_flow(self):
        # Main game flow bridge:
        # 1) Deal 13 cards
        # 2) Configure 3-5-5 lane hands
        # 3) Run final betting round, which leads to showdown -> determine_winner_by_lanes
        self.deal_initial_hands()
        print_output = not bool(self.action_callback)
        self.configure_player_splits(print_output=print_output)
        self.betting_round(minimum_bet=self.minimum_bet, round_name="final_betting_round")
    
    def betting_round(self, minimum_bet=10, round_name="betting_round"):
        print(f"DEBUG: Starting betting round: {round_name} with minimum bet: {minimum_bet}")
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
                self._run_post_initial_round_flow()
            elif self.current_round_number == 2:
                self.showdown()
        self._betting_done_callback = done_callback
        self.betting_run()
        pass
    
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
    
    def showdown(self):
        print(f"The final pot total is: {self.pot}\n")
        self.show_hands()
        self.determine_winner_by_lanes()
    
    def award_player(self,player : Player,bet: int):
        player.win_bet(bet)

    def _normalize_card_list(self, value):
        cards = []

        def collect(item):
            if isinstance(item, str):
                cards.append(item)
            elif isinstance(item, (list, tuple)):
                for nested_item in item:
                    collect(nested_item)

        collect(value)
        return cards

    def _resolve_lane_winner(self, lane_attr):
        highest_rank = 0
        winning_hand = []
        winning_hand_name = ""
        winners = []
        
        players = [p for p in self.players if not p.isFolded]
        for player in players:

            hand = list(getattr(player, lane_attr, []) or [])
            if not hand:
                continue

            rank, result, hand_name = self.evaluator.evaluate_hand(hand, [])
            result_cards = self._normalize_card_list(result)
            if rank > highest_rank:
                highest_rank = rank
                winning_hand = result
                winning_hand_name = hand_name
                winners = [player]

            if rank == highest_rank and winners:
                winning_hand_cards = self._normalize_card_list(winning_hand)
                # Precompute highest card ranks for both current winner and player
                highest_rank_winner = self.evaluator.get_highest_rank(winning_hand_cards)
                highest_rank_player = self.evaluator.get_highest_rank(result_cards)
                # Check suits and highest card to break ties.
                # This is a simplified tie-breaking logic and may not cover all cases.

                if (rank in [2, 3]):  # Pair, Two Pair
                    # Determine pair ranks for winner and player (two ranks for Two Pair)
                    def get_pair_ranks(cards):
                        ranks = [self.evaluator.remove_suit_card(c) for c in cards]
                        unique = sorted(set(ranks), key=lambda r: self.rank_list.index(r), reverse=True)
                        return unique

                    winner_pair_ranks = get_pair_ranks(winning_hand_cards)
                    player_pair_ranks = get_pair_ranks(result_cards)

                    # Compare highest pair first
                    def rank_val(r):
                        return self.rank_list.index(r)

                    if rank_val(player_pair_ranks[0]) > rank_val(winner_pair_ranks[0]):
                        winning_hand = result
                        winning_hand_name = hand_name
                        winners = [player]
                    elif rank_val(player_pair_ranks[0]) == rank_val(winner_pair_ranks[0]):
                        if len(player_pair_ranks) == 2 and len(winner_pair_ranks) == 2:
                            # Two Pair: compare second pair
                            if rank_val(player_pair_ranks[1]) > rank_val(winner_pair_ranks[1]):
                                winning_hand = result
                                winning_hand_name = hand_name
                                winners = [player]
                            elif rank_val(player_pair_ranks[1]) == rank_val(winner_pair_ranks[1]):
                                # Compare kickers (hand minus the pair cards)
                                leader_hand = list(getattr(winners[0], lane_attr, []) or [])
                                leader_kickers = [c for c in leader_hand if c not in winning_hand]
                                player_kickers = [c for c in hand if c not in result]
                                winner_high_card = self.evaluator.get_highest_rank(leader_kickers)
                                player_high_card = self.evaluator.get_highest_rank(player_kickers)
                                if player_high_card > winner_high_card:
                                    winning_hand = result
                                    winning_hand_name = hand_name
                                    winners = [player]
                                elif player_high_card == winner_high_card:
                                    # Two Pair: if kickers equal, it's a tie (no suit precedence)
                                    if player not in winners:
                                        winners.append(player)
                        else:
                            # Single Pair: compare kickers after equal pair rank
                            leader_hand = list(getattr(winners[0], lane_attr, []) or [])
                            leader_kickers = [c for c in leader_hand if c not in winning_hand]
                            player_kickers = [c for c in hand if c not in result]
                            winner_high_card = self.evaluator.get_highest_rank(leader_kickers)
                            player_high_card = self.evaluator.get_highest_rank(player_kickers)
                            if player_high_card > winner_high_card:
                                winning_hand = result
                                winning_hand_name = hand_name
                                winners = [player]
                            elif player_high_card == winner_high_card:
                                # Only pairs use suit precedence
                                winner_high_suit = self.evaluator.get_highest_suit(winning_hand_cards)
                                player_high_suit = self.evaluator.get_highest_suit(result_cards)
                                suit_rank = {"H": 4, "D": 3, "C": 2, "S": 1}
                                if suit_rank[player_high_suit] > suit_rank[winner_high_suit]:
                                    winning_hand = result
                                    winning_hand_name = hand_name
                                    winners = [player]
                elif (rank == 4):
                    # Three of a kind: compare card ranks.
                    # STOP GENERATING FOR KICKERS. YOU CANT HAVE TWO PLAYERS WITH THE SAME THREE OF A KIND.
                    # THERE AREN'T ENOUGH CARDS IN THE DECK FOR THAT TO HAPPEN.
                    if highest_rank_player > highest_rank_winner:
                        winning_hand = result
                        winning_hand_name = hand_name
                        winners = [player]
                elif rank == 7:  # Full House
                    # We only need to compare the ranks of the three of a kind part of the full house.
                    # The pair is unnecessary because its impossible to share three of a kinds.
                    # There are only four of each rank, thus its impossible for two players
                    # to have three of a kinds of the same rank in the same hand.
                    three_card_winner = self.evaluator.remove_suit_card(winning_hand[0])
                    three_card_player = self.evaluator.remove_suit_card(result[0])
                    if three_card_player > three_card_winner:
                        winning_hand = result
                        winning_hand_name = hand_name
                        winners = [player]
                    elif three_card_player == three_card_winner:
                        # Treat as tie; suits are not compared for full house
                        if player not in winners:
                            winners.append(player)
                elif rank in [5, 6, 8, 9]:  # Straight, Flush, Four of a Kind, Straight Flush
                    # For these hand ranks, compare highest card first, then next highest cards if needed.
                    if highest_rank_player > highest_rank_winner:
                        winning_hand = result
                        winning_hand_name = hand_name
                        winners = [player]
                    else:
                        # If highest ranks are equal, compare the next highest cards until a difference is found.
                        # If no difference is found, treat as tie.
                        sorted_winner_hand = self.evaluator.sort_hand(winning_hand_cards)
                        sorted_player_hand = self.evaluator.sort_hand(result_cards)
                        decided = False
                        for w_card, p_card in zip(reversed(sorted_winner_hand), reversed(sorted_player_hand)):
                            if self.evaluator.remove_suit_card(p_card) > self.evaluator.remove_suit_card(w_card):
                                winning_hand = result
                                winning_hand_name = hand_name
                                winners = [player]
                                decided = True
                                break
                        # If ranks compare equal across all cards, it's a tie (no suit comparison here)
                        if not decided and highest_rank_player == highest_rank_winner:
                            if player not in winners:
                                winners.append(player)
                elif rank == 10:  # Royal Flush
                    # Royal flushes tie automatically
                    if player not in winners:
                        winners.append(player)
                else:  # High Card
                    if highest_rank_player > highest_rank_winner:
                        winning_hand = result
                        winning_hand_name = hand_name
                        winners = [player]
                    elif highest_rank_player == highest_rank_winner:
                        # If highest ranks are equal, compare suits of the highest card
                        winner_high_suit = self.evaluator.get_highest_suit(winning_hand_cards)
                        player_high_suit = self.evaluator.get_highest_suit(result_cards)
                        suit_rank = {"H": 4, "D": 3, "C": 2, "S": 1}
                        if suit_rank[player_high_suit] > suit_rank[winner_high_suit]:
                            winning_hand = result
                            winning_hand_name = hand_name
                            winners = [player]

        return {
            "winners": winners,
            "winning_hand": self._normalize_card_list(winning_hand),
            "hand_name": winning_hand_name,
        }

    def determine_winner_by_lanes(self):
        # 13-card resolution: determine winners for Front/Middle/Back lanes
        # using determine_winner tie-break logic, then settle by lane majority.
        players = [p for p in self.players if not p.isFolded]

        if not players:
            return

        front_resolution = self._resolve_lane_winner("front_hand")
        middle_resolution = self._resolve_lane_winner("middle_hand")
        back_resolution = self._resolve_lane_winner("back_hand")

        lane_results = {
            "front": {
                "winner_names": [winner.name for winner in front_resolution["winners"]],
                "winner": front_resolution["winners"][0].name if len(front_resolution["winners"]) == 1 else "Tie",
                "hand_name": front_resolution["hand_name"],
                "winning_hand": front_resolution["winning_hand"],
            },
            "middle": {
                "winner_names": [winner.name for winner in middle_resolution["winners"]],
                "winner": middle_resolution["winners"][0].name if len(middle_resolution["winners"]) == 1 else "Tie",
                "hand_name": middle_resolution["hand_name"],
                "winning_hand": middle_resolution["winning_hand"],
            },
            "back": {
                "winner_names": [winner.name for winner in back_resolution["winners"]],
                "winner": back_resolution["winners"][0].name if len(back_resolution["winners"]) == 1 else "Tie",
                "hand_name": back_resolution["hand_name"],
                "winning_hand": back_resolution["winning_hand"],
            },
        }

        lane_winners = []
        if len(front_resolution["winners"]) == 1:
            lane_winners.append(front_resolution["winners"][0])
        if len(middle_resolution["winners"]) == 1:
            lane_winners.append(middle_resolution["winners"][0])
        if len(back_resolution["winners"]) == 1:
            lane_winners.append(back_resolution["winners"][0])

        if len(lane_winners) == 3 and len({winner.name for winner in lane_winners}) == 3:
            winners = players
        else:
            lane_win_counts = Counter(winner.name for winner in lane_winners)
            if not lane_win_counts:
                winners = players
            else:
                max_wins = max(lane_win_counts.values())
                if max_wins >= 2:
                    winners = [player for player in players if lane_win_counts.get(player.name, 0) == max_wins]
                else:
                    winners = players

        winner_names = [player.name for player in winners]
        if self.phase_callback:
            self.phase_callback(
                "winner",
                {
                    "winner_names": winner_names,
                    "winning_hand": [],
                    "lane_results": lane_results,
                    "pot": self.pot,
                },
            )

        print(
            f"Lane results -> "
            f"Front: {lane_results['front']['winner']} ({lane_results['front']['hand_name']}), "
            f"Middle: {lane_results['middle']['winner']} ({lane_results['middle']['hand_name']}), "
            f"Back: {lane_results['back']['winner']} ({lane_results['back']['hand_name']})"
        )

        if len(winners) > 1:
            print(f"Tie: {', '.join(winner_names)}")
            share = self.pot // len(winners)
            remainder = self.pot % len(winners)
            for idx, winner in enumerate(winners):
                award = share + (remainder if idx == 0 else 0)
                self.award_player(winner, award)
                self.db_helper.update_player_stats(winner.name, award, True, award)
            self.db_helper.log_game("Thirteen Card Poker", ', '.join([p.name for p in players]), ', '.join(winner_names), self.pot)
        else:
            leader = winners[0]
            print(f"The winner is {leader.name} by lane majority (2 of 3).")
            self.award_player(leader, self.pot)
            self.db_helper.log_game("Thirteen Card Poker", ', '.join([p.name for p in players]), leader.name, self.pot)
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
        # main_player.hand = ["9C", "10C", "JC", "QC", "KC"]  # Royal Flush
        # self.player_nodes[1].player.hand = ["9D", "10D", "JD", "QD", "KD"]  # Straight Flush
        # self.player_nodes[2].player.hand = ["2C", "2D", "2H", "5S", "7D"]  # Three of a Kind
    
    def debug_start_game(self):
        self.betting_round(minimum_bet=self.minimum_bet, round_name="initial_betting_round")
        
        
    def start_game(self):
        # self.debug_start_game()
        # return
        #self.deal_initial_hands()
        #For thirteen card poker, we start with bets then deal thirteen cards.
        #We then have the players arrange their cards in 3, 5, and 5 hands.
        #CLI default: auto-arrange only bot players.
        #Human player is an exception: only 3/5/5 split is enforced.
        #The back hand does not have to be the strongest.
        #The goal is to win 2/3 of the hands to win the pot.
        #It is impossible for a tie to occur.
        
        self.betting_round(minimum_bet=self.minimum_bet, round_name="initial_betting_round")
        
        
    def show_hands(self):
        for player in self.players:
            has_split = (
                hasattr(player, "front_hand")
                and hasattr(player, "middle_hand")
                and hasattr(player, "back_hand")
                and len(getattr(player, "front_hand", [])) == 3
                and len(getattr(player, "middle_hand", [])) == 5
                and len(getattr(player, "back_hand", [])) == 5
            )

            if has_split:
                front_hand = list(player.front_hand)
                middle_hand = list(player.middle_hand)
                back_hand = list(player.back_hand)

                front_name = self.get_hand_name(front_hand)
                middle_name = self.get_hand_name(middle_hand)
                back_name = self.get_hand_name(back_hand)

                front_display = show_substituted(self._sort_hand_for_display(front_hand))
                middle_display = show_substituted(self._sort_hand_for_display(middle_hand))
                back_display = show_substituted(self._sort_hand_for_display(back_hand))

                print(
                    f"{player.name}:\n"
                    f"Front({front_name})={front_display} | "
                    f"Middle({middle_name})={middle_display} | "
                    f"Back({back_name})={back_display}"
                )
            else:
                print(f"{player.name}'s hand: {show_substituted(player.hand)}")
            
    def show_only_player_hand(self):
        main_player_node = next(node for node in self.player_nodes if not node.player.isBot)
        main_player = main_player_node.player
        print(f"{main_player.name}'s hand: {show_substituted(main_player.hand)}")
        #return main_player.hand

if "__main__" == __name__:
    game = ThirteenCardPoker(player_names=["You", "Bot1", "Bot2"])
#     game.set_debug_hands({
#     "You": ["AH","KH","QH","JH","10H"],
#     "Bot1": ["9C","9D","9S","2H","3D"],
#     "Bot2": ["AS","AD","AC","KS","QD"],
# })
    game.start_game()














