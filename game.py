
import random


cards=[]
suit=["H", "D", "C", "S"]
rank = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
substitute=["1","11","12","13"]

for y in suit:
    for x in rank:
        cards.append(str(x)+y)
#print (cards)

def custom_sort(hand):
    sorted_hand=[]
    
    for card in cards:
        if card in hand:
            sorted_hand.append(card)

    return sorted_hand

def remove_suit(hand):
    temp_hand=[]
    for card in hand:
        temp_hand.append(card[:-1])
    return temp_hand
    
def show_substituted(hand):
    if isinstance(hand, str):
        hand = [hand]
    substituted_hand = []
    #print (hand)
    for card in hand:
        rank_part = card[:-1]
        suit_part = card[-1]
        # print (rank_part)
        # print (suit_part)
        if rank_part == "1":
            substituted_hand.append("A" + suit_part)
        elif rank_part == "11":
            substituted_hand.append("J" + suit_part)
        elif rank_part == "12":
            substituted_hand.append("Q" + suit_part)
        elif rank_part == "13":
            substituted_hand.append("K" + suit_part)
        else:
            substituted_hand.append(card)
    return substituted_hand

class Poker_Win_Determination():
    def evaluate_hand(self, hand, dealt):
        checks = [
                (self.check_royal_flush, 10, "Royal Flush"),
                (self.check_straight_flush, 9, "Straight Flush"),
                (self.check_four_of_a_kind, 8, "Four of a Kind"),
                (self.check_full_house, 7, "Full House"),
                (self.check_flush, 6, "Flush"),
                (self.check_straight, 5, "Straight"),
                (self.check_three_of_a_kind, 4, "Three of a Kind"),
                (self.check_two_pair, 3, "Two Pair"),
                (self.check_single_pair, 2, "Pair"),
            ]
        for check_func, rank, name in checks:
            check, result = check_func(hand, dealt)
            if check:
                return rank, result, name
        # If no hand found, return high card
        high_card = self.get_high_card(hand, dealt)
        return 1, high_card, "High Card"
    
    def check_royal_flush(self, hand, dealt):
        temp_hand=hand.copy() + dealt.copy()
        hand = custom_sort(temp_hand)
        royal_flushes = [
            [ "AH", "10H", "JH", "QH", "KH",],
            ["AD","10D", "JD", "QD", "KD"],
            ["AC","10C", "JC", "QC", "KC"],
            ["AS", "10S", "JS", "QS", "KS"]
        ]
        for rf in royal_flushes:
            if all(card in hand for card in rf):
                return True, rf
        return False, []
        
    def check_straight_flush(self,hand, dealt):
        def check_straight(self,hand,dealt):
            temp_hand=hand.copy() + dealt.copy()
            temp_hand=remove_suit(temp_hand)
            temp_hand.sort()
            pointA, pointB=0, 5
            while pointA<len(rank)-5:
                pointHandA, pointHandB=0,5
                while pointHandA<len(temp_hand)-5:
                    if temp_hand[pointHandA:pointHandB]==rank[pointA:pointB]:
                        print(temp_hand[pointHandA:pointHandB], rank[pointA:pointB])
                        return True, temp_hand[pointHandA:pointHandB]
                    pointHandA, pointHandB = pointHandA + 1, pointHandB + 1
                pointA, pointB = pointA + 1, pointB + 1
            return False, []
        
        firstCheck, straightCards=check_straight(self,hand, dealt)
        
        if (firstCheck):
            suits=["H", "D", "C", "S"]
            for suit in suits:
                suitedCards=[]
                for card in straightCards:
                    suitedCards.append(card+suit)
                temp_hand=hand.copy()
                temp_hand=temp_hand+dealt
                if all(card in temp_hand for card in suitedCards):
                    return True, suitedCards
        return False, []
    
    def check_straight(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        for i in range (len(temp_hand)):
            temp_hand[i]=temp_hand[i][:-1]
        temp_hand.sort()
        pointA, pointB=0, 5
        while pointA<len(rank)-5:
            pointHandA, pointHandB=0, 5
            while pointHandA<len(temp_hand)-5:
                if temp_hand[pointHandA:pointHandB]==rank[pointA:pointB]:
                    print(temp_hand[pointHandA:pointHandB], rank[pointA:pointB])
                    return True, temp_hand[pointHandA:pointHandB]
                pointHandA, pointHandB = pointHandA + 1, pointHandB + 1
            pointA, pointB = pointA + 1, pointB + 1
        return False, []
    
    def check_four_of_a_kind(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        temp_hand_ranks=remove_suit(temp_hand)
        for card_rank in rank:
            if temp_hand_ranks.count(card_rank)==4:
                # Collect the actual cards with suits
                four_cards = [c for c in temp_hand if c[:-1] == card_rank]
                return True, four_cards
        return False, []
    
    def check_three_of_a_kind(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        temp_hand_ranks=remove_suit(temp_hand)
        for card_rank in rank:
            if temp_hand_ranks.count(card_rank)==3:
                three_cards = [c for c in temp_hand if c[:-1] == card_rank]
                return True, three_cards
        return False, []
    
    def check_single_pair(self,hand,dealt):
        
        temp_hand=hand.copy() + dealt.copy()
        temp_hand_ranks=remove_suit(temp_hand)
        for card_rank in rank:
            if temp_hand_ranks.count(card_rank) == 2:
                pair_cards = [c for c in temp_hand if c[:-1] == card_rank]
                return True, pair_cards
        return False, []
    
    def check_two_pair(self,hand,dealt):
        temp_hand = hand.copy() + dealt.copy()
        temp_hand_ranks = remove_suit(temp_hand)
        pairs = []
        # Find the two ranks that have exactly two cards
        for card in rank:
            if temp_hand_ranks.count(card) == 2 and card not in pairs:
                pairs.append(card)
            if len(pairs) == 2:
                # Now collect the actual cards (with suits) for these two pairs
                pair_cards = []
                for pair_rank in pairs:
                    pair_cards.extend([c for c in temp_hand if c[:-1] == pair_rank])
                return True, pair_cards
        return False, []
    
    def check_full_house(self,hand,dealt):
        threeCheck, threeCard=self.check_three_of_a_kind(hand, dealt)
        pairCheck, pairCards=self.check_single_pair(hand, dealt)
        if (threeCheck and pairCheck):
            if (threeCard not in pairCards):
                return True, (threeCard, pairCards)
        return False, []

    def check_flush(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        suits=["H", "D", "C", "S"]
        for suit in suits:
            suitedCards=[]
            for card in temp_hand:
                if card[-1]==suit:
                    suitedCards.append(card)
            if len(suitedCards)>=5:
                return True, suitedCards
        return False, []
    
    def get_high_card(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        temp_hand=custom_sort(temp_hand)
        return temp_hand[-1]

class Dealer():
    def __init__(self):
        deck = cards.copy()
        random.shuffle(deck)
        self.deck = deck
        self.hand=[]
        
    def deal_card(self):
        card = self.deck.pop()
        return card
    
    def deal_self(self):
        card = self.deal_card()
        self.hand.append(card)
    
    def show_hand(self):
        return self.hand

# Linked list node for players
class PlayerNode:
    def __init__(self, player):
        self.player = player
        self.next = None
        self.prev = None

class Player():
    def __init__(self,name, isBot=True, wallet=1000, bet_callback=None):
        self.name=name
        self.hand=[]
        self.table=[]
        self.wallet=wallet
        self.bet=0
        self.current_bet=0
        self.isBot=isBot
        self.risk_tolerance=random.choice(["low","medium","high"])
        self.isFolded=False
        self.bet_callback = bet_callback
        if isBot:
            self.evaluater = Poker_Win_Determination()
        
    def request_card(self, dealer):
        card = dealer.deal_card()
        self.hand.append(card)
        
    def add_bet(self, amount):
        if amount <= self.wallet:
            self.bet += amount
            self.current_bet += amount
            self.wallet -= amount
            return True
        else:
            print(f"{self.name} does not have enough funds to bet {amount}.")
            return False
        
    def win_bet(self,amount):
        self.wallet += amount
        print(f"{self.name} wins {amount}! New wallet balance: {self.wallet}")
        self.reset()
        
    def reset(self):
        self.hand=[]
        self.table=[]
        self.bet=0
        self.current_bet=0
        self.isFolded=False
        self.isAllIn=False
        
    def lose_bet(self):
        self.reset()
    
    def add_to_bet(self, amount):
        if self.add_bet(amount):
            print(f"{self.name} has increased their bet by {amount}. Current bet: {self.current_bet}. Remaining funds: {self.wallet}")
        else:
            print(f"{self.name} could not increase their bet by {amount} due to insufficient funds.")
            
    def set_bet(self, minimum_bet, round_number = None):
        if self.bet_callback:
            self.bet_callback(self, minimum_bet)
            return
        
        if (self.wallet <=0):
            print(f"{self.name} has no funds left to bet. Skipping turn.")
            return
        if (minimum_bet > self.wallet):
            minimum_bet = self.wallet
            print (f"{self.name} is going all-in with {minimum_bet}.")
            self.add_bet(minimum_bet)
            return
        
        input_amount = input(f"{self.name}, enter your bet amount (Available funds: {self.wallet}): ")
        try:
            amount = int(input_amount)
            if amount >= minimum_bet and amount <= self.wallet:
                print(f"{self.name} has placed a bet of {amount}. Remaining funds: {self.wallet}")
                self.add_bet(amount)
            else:
                print(f"Invalid bet amount. Please enter a positive number up to {self.wallet}.")
                self.set_bet(minimum_bet)
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
            self.set_bet(minimum_bet)
        
    
class BotPlayer(Player):
    def __init__(self, name, wallet=1000):
        super().__init__(name, wallet)
        self.isBot = True
        self.risk_tolerance = random.choice(["low", "medium", "high"])
        self.evaluater = Poker_Win_Determination()
        
    def set_bet(self, minimum_bet, round_number = None):
    
        #Check hand strength
        hand_strength=self.bot_assess_hand_strength(self.hand, self.table)
        #Determine maximum bet
        self.determine_maximum_bet(round_number=round_number)
        
        bet = minimum_bet #Default to call
        
        #---------------------------------
        #Cannot Continue Playing Scenarios
        #---------------------------------
        if self.wallet <=0:
            print(f"{self.name} (Bot) has no funds left to bet. Skipping turn.")
            return
        if self.isFolded:
            print(f"{self.name} (Bot) has already folded. Skipping turn.")
            return
        #---------------------------------
        #Check for Check Scenario
        #---------------------------------
        if (minimum_bet == 0):
            if (hand_strength<1):
                print (f"{self.name} (Bot) decides to check.")
                return
            else:
                bet = random.randint(10, min(50, self.wallet))
                print (f"{self.name} (Bot) decides to bet {bet} instead of checking.")
                return
        #---------------------------------
        #All-in Scenario
        #---------------------------------
        elif (minimum_bet > self.wallet):
            minimum_bet = self.wallet
            #Pair or worse, don't do it.
            if (hand_strength<=1):
                self.isFolded=True
                print(f"{self.name} (Bot) decides to fold as it does not want to\n"+
                      f"all-in on the bet of {minimum_bet}.")
            #Three of a kind or better, go for it.
            elif (hand_strength>1):
                print (f"{self.name} (Bot) is going all-in with {minimum_bet}.")
                self.add_bet(minimum_bet)
            return
        #---------------------------------
        #Call/Raise Scenario
        #---------------------------------
        else:
            maximum_bet = self.maximum_bet
            #If the requirement to call, is greater than the maximum_bet minus
            #the existing current_bet (already placed bet)
            if (minimum_bet > maximum_bet-self.current_bet):
                #If the requirement to call is not 1.5 times more than the remaining allowable bet
                if (minimum_bet*1.5 <= maximum_bet-self.current_bet):
                    #Make the bet.
                    if (hand_strength<=1):
                        self.isFolded=True
                        print(
                            f"{self.name} (Bot) decides to fold as the minimum bet {minimum_bet}\n"
                            f"+ existing bet of {self.current_bet} exceeds its maximum willingness to bet {maximum_bet}."
                        )
                        return
                    #Three of a kind or better, go for it.
                    elif (hand_strength>1):
                        print (f"{self.name} (Bot) has called. Remaining funds: {self.wallet}")
                        bet=minimum_bet
                else:
                    # Bluffing chance
                    randomNumber=random.random()
                    print(f"Random number for bluff decision: {randomNumber}")
                    if (randomNumber>0.9):
                        print(f"{self.name} (Bot) thinks you are bluffing and matches your bet\n" +
                                f"despite the odds.")
                        bet=minimum_bet
                    else:
                        print(
                            f"{self.name} (Bot) decides to fold as the minimum bet {minimum_bet}\n"
                            f"+ existing bet of {self.current_bet} exceeds its maximum willingness to bet {maximum_bet}."
                        )
                        self.isFolded=True
                        return
            else:
                if (minimum_bet > maximum_bet):
                    print(
                        f"{self.name} (Bot) decides to fold as the minimum bet {minimum_bet}\n"
                        f"+ existing bet of {self.current_bet} exceeds its maximum willingness to bet {maximum_bet}."
                    )
                    self.isFolded=True
                    return
                
                if (self.risk_tolerance=="low" and self.current_bet >= maximum_bet*0.5):
                    #bet = minimum_bet
                    pass
                elif (self.risk_tolerance=="medium" and self.current_bet >= maximum_bet*0.7):
                    bet = random.randint(minimum_bet, int(maximum_bet*0.7))
                else:
                    bet = random.randint(minimum_bet, min(maximum_bet, self.wallet))
        
        if bet is not None:
            self.add_bet(bet)
            if (bet == minimum_bet):
                print (f"{self.name} (Bot) has called. Remaining funds: {self.wallet}")
            else:
                print(f"{self.name} (Bot) has raised their bet by {bet}. Remaining funds: {self.wallet}")
        
    def determine_maximum_bet(self, round_number=None):
        self.maximum_bet=int(100*self.bot_assess_risk(self) + 100* self.bot_assess_hand_strength(self.hand, self.table))
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
    
    def bot_assess_risk(self, bot):
        if bot.risk_tolerance == "low":
            return 0.2
        elif bot.risk_tolerance == "medium":
            return 0.5
        else:  # high risk tolerance
            return 1
    
    
    def bot_assess_hand_strength(self, hand, dealt):
        rank, result, name = self.evaluater.evaluate_hand(hand, dealt)
        print (f"{self.name} (Bot) assesses its hand as a {name}.")
        if rank >= 7:  # Full House or better
            return 3.0
        elif rank >= 4:  # Three of a Kind to Straight
            return 1.5
        elif rank >= 2:  # Pair to Two Pair
            return 1
        else:  # High Card
            return 0.5
    
import database
class Database_Helper():
    def requires_player(func):
        def wrapper(self, player_name, *args, **kwargs):
            if player_name in self.players:
                return func(self, player_name, *args, **kwargs)
            else:
                return None
        return wrapper

    def __init__(self):
        self.db = database.gameDatabase()
        self.players =self.retrieve_list_of_players()
    def log_game(self, game_type, players, winner, pot):
        self.db.log_game(game_type, players, winner, pot)
        print(f"{game_type} Game logged to database.")
    
    
    @requires_player
    def retrieve_player_wallet(self, player_name):
        player = self.db.get_player(player_name)
        return player['wallet'] if player else None
    
    def retrieve_list_of_players(self):
        return self.db.get_players()
    
    def add_player(self, player_name):
        self.db.add_player(player_name)
        print(f"Player {player_name} added to database.")
    
    
    @requires_player
    def update_player_stats(self, player_name, wallet_change, won_game, winnings):
        self.db.update_player_stats(player_name, wallet_change, won_game, winnings)

    @requires_player
    def update_player_wallet(self, player_name, amount):
        self.db.update_player_wallet(player_name, amount)

    @requires_player
    def player_take_loan(self, player_name):
        self.db.player_take_loan(player_name)

    @requires_player
    def get_player_debt(self, player_name):
        player = self.db.get_player(player_name)
        return player['debt'] if player else None
    
# x = Database_Helper()
# x.add_player("Dev")
# x.retrieve_player_wallet("Dev")
class Poker_for_GUI(Poker_Win_Determination):
    def __init__(self, player_names,
                 bet_callback=None,
                 phase_callback=None,
                 pot_update_callback=None,
                 bot_bet_update_callback=None,
                 bot_fold_callback=None):
        self.dealer = Dealer()
        self.db_helper= Database_Helper()
        
        wallet = self.db_helper.retrieve_player_wallet(player_names[0])
        override = False
        if override:
            wallet = 1000
        elif wallet is None:
            wallet = 1000 #Default
        elif wallet <= 0:
            self.db_helper.player_take_loan(player_names[0])

        # Create the user player with the correct wallet
        user_player = Player(player_names[0], bet_callback=bet_callback, isBot=False, wallet=wallet)
        bot_players = [BotPlayer(f"Bot{i}") for i in range(1, len(player_names))]
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
        
        
        self.bet_callback = bet_callback
        self.phase_callback = phase_callback
        self.pot_update_callback = pot_update_callback
        self.bot_bet_update_callback = bot_bet_update_callback
        self.bot_fold_callback = bot_fold_callback
        
        self._betting_iter = None
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
        self._betting_iter = iter(active_players)
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

        wallet_before = player.wallet
        if player.isBot:
            player.set_bet(to_call, round_number=self._current_round_number)
            wallet_after = player.wallet
            delta = wallet_after - wallet_before
            self.pot = sum(node.player.bet for node in self.player_nodes)
            if self.pot_update_callback:
                self.pot_update_callback(self.pot)
            bot_index = self.players.index(player) - 1  # Adjust for human player at index 0
            if self.bot_bet_update_callback:
                self.bot_bet_update_callback(bot_index, player.current_bet)
            self.db_helper.update_player_wallet(player.name, delta)
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
            if self.bet_callback:
                self._last_human_node = node  # Save for resume
                self._last_human_bet = player.current_bet  # Save for resume
                self.bet_callback(to_call)
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
    
    def determine_winner(self, players, dealt):
        winner= None
        highest_rank=0
        winning_hand=[]
        players = [p for p in players if not p.isFolded]
        for player in players:
            hand = player.hand
            rank, result, hand_name = self.evaluate_hand(hand, dealt)
            print(f"{player.name} has {hand_name}: {show_substituted(result)}")
            if rank > highest_rank:
                highest_rank = rank
                winner = player
                winning_hand = result
        print(f"The winner is {winner.name} with hand: {show_substituted(winning_hand)}")
        self.award_player(winner, self.pot)
        self.db_helper.log_game("Poker", ', '.join([p.name for p in players]), winner.name, self.pot)
        self.db_helper.update_player_stats(winner.name, self.pot, True, self.pot)
        

    def award_player(self,player,bet):
        player.win_bet(bet)

    
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