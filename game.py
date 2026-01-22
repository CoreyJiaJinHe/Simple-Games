
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
    def __init__(self,name, isBot=True):
        self.name=name
        self.hand=[]
        self.table=[]
        self.wallet=1000
        self.bet=0
        self.current_bet=0
        self.isBot=isBot
        self.risk_tolerance=random.choice(["low","medium","high"])
        self.isFolded=False
        
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
            self.current_bet += amount
            print(f"{self.name} has increased their bet by {amount}. Current bet: {self.current_bet}. Remaining funds: {self.wallet}")
        else:
            print(f"{self.name} could not increase their bet by {amount} due to insufficient funds.")
            
    def set_bet(self, minimum_bet):
        if not self.isBot:
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
                if self.add_bet(amount) and amount >= minimum_bet:
                    print(f"{self.name} has placed a bet of {amount}. Remaining funds: {self.wallet}")
                else:
                    print(f"Invalid bet amount. Please enter a positive number up to {self.wallet}.")
                    self.set_bet(minimum_bet)
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
                self.set_bet(minimum_bet)
        else:
            if self.wallet <=0:
                print(f"{self.name} (Bot) has no funds left to bet. Skipping turn.")
                return
            if self.isFolded:
                print(f"{self.name} (Bot) has already folded. Skipping turn.")
                return
            self.determine_maximum_bet()
            maximum_bet = self.maximum_bet
            if (minimum_bet > self.wallet):
                minimum_bet = self.wallet
                print (f"{self.name} (Bot) is going all-in with {minimum_bet}.")
                self.add_bet(minimum_bet)
                return
            else:
                #If the minimum bet is higher than the maximum bet, but not by too much, set max to min
                #and allow the bot to bet
                if (minimum_bet > maximum_bet and minimum_bet*1.5 < maximum_bet):
                    maximum_bet = minimum_bet
                    amount = random.randint(minimum_bet, min(int(maximum_bet * 100), self.wallet))
                    self.add_bet(amount)
                    print(f"{self.name} (Bot) has placed a bet of {amount}. Remaining funds: {self.wallet}")
                else:
                    if (maximum_bet < minimum_bet):
                        print(f"{self.name} (Bot) decides to fold as the minimum bet {minimum_bet} exceeds its maximum willingness to bet {maximum_bet}.")
                        self.isFolded=True
                        return
                    amount = random.randint(minimum_bet, min(int(maximum_bet * 100), self.wallet))
                    self.add_bet(amount)
                    print(f"{self.name} (Bot) has placed a bet of {amount}. Remaining funds: {self.wallet}")
    def determine_maximum_bet(self):
        self.maximum_bet=100*self.bot_assess_risk(self) + 100* self.bot_assess_hand_strength(self.hand, self.table)
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
        evaluater = Poker([])
        rank, result, name = evaluater.evaluate_hand(hand, dealt)
        if rank >= 7:  # Full House or better
            return 3.0
        elif rank >= 4:  # Three of a Kind to Straight
            return 1.5
        elif rank >= 2:  # Pair to Two Pair
            return 1
        else:  # High Card
            return 0.5


class Poker():
    def __init__ (self, player_names):
        self.dealer = Dealer()
        self.players = [Player(name, isBot=(name!="You")) for name in player_names]
        
        # Create circular linked list of players
        self.player_nodes = [PlayerNode(p) for p in self.players]
        n = len(self.player_nodes)
        for i in range(n):
            self.player_nodes[i].next = self.player_nodes[(i+1)%n]
            self.player_nodes[i].prev = self.player_nodes[(i-1)%n]
        
        self.dealt = []
        self.pot = 0
        self.minimum_bet = 10
    def deal_initial_hands(self):
        for _ in range(2):  # Deal 2 cards to each player
            for player in self.players:
                player.request_card(self.dealer)
    
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
        
    def show_hands(self):
        for player in self.players:
            print(f"{player.name}'s hand: {show_substituted(player.hand)}")
    
    def betting_round(self):
        print("\n--- Betting Round ---")
        # Reset all current_bet to 0 for this round
        for node in self.player_nodes:
            node.player.current_bet = 0
        current_bet = self.minimum_bet
        # Start from first player
        start = self.player_nodes[0]
        node = start
        last_raiser = None
        
        # Check if there is more than one active player
        active_players = [n for n in self.player_nodes if not n.player.isFolded and n.player.wallet > 0]
        if len(active_players) < 2:
            print("No betting needed: only one player remains.")
            return
        
        while True:
            player = node.player
            if player.isFolded or player.wallet <= 0:
                node = node.next
                if node == start:
                    break
                continue
            
            to_call = current_bet - player.current_bet
            # Only ask to bet if player has not matched current bet
            if player.wallet > 0 and player.current_bet < current_bet or last_raiser == node:
                player.set_bet(to_call)
                if player.current_bet > current_bet:
                    # If raised, all previous players must match
                    current_bet = player.current_bet
                    last_raiser = node
                    # Go back to previous players to let them match
                    prev = node.prev
                    while prev != node:
                        prev_player = prev.player
                        if prev_player.current_bet < current_bet and prev_player.wallet > 0:
                            print(f"{prev_player.name} must match the new bet of {current_bet}.")
                            prev_player.set_bet(current_bet - prev_player.current_bet)
                        prev = prev.prev
                        if prev == last_raiser:
                            break
            node = node.next
            if node == start:
                break
        # Add all bets to pot
        self.pot = sum(node.player.bet for node in self.player_nodes)
        print(f"Total pot is now: {self.pot}\n")
        
    
    def game_phases(self):
        self.deal_initial_hands()
        self.show_hands()
        
        self.betting_round()
        
        flop = self.deal_flop()
        print(f"Flop: {show_substituted(flop)}")
        self.dealt = flop.copy()
        
        self.betting_round()
        turn = self.deal_turn()
        print(f"Turn: {show_substituted([turn])}")
        self.dealt = self.dealt + [turn]
        
        self.betting_round()
        river = self.deal_river()
        print(f"River: {show_substituted([river])}")
        
        self.dealt = self.dealt + [river]
        print(f"Dealt cards: {show_substituted(self.dealt)}")
        self.betting_round()
        
        print("\n--- Determining Winner ---")
        print(f"Dealt cards: {show_substituted(self.dealt)}")
        self.determine_winner(self.players, self.dealt)
    
        #self.show_hands()
        
    def determine_winner(self, players, dealt):
        # Placeholder for winner determination logic
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

    def award_player(self,player,bet):
        player.win_bet(bet)

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
x = Poker(["You", "Bob"])
x.game_phases()
