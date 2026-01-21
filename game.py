
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
        self.wallet=1000
        self.bet=0
        self.current_bet=0
        self.isBot=isBot
        
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
        self.bet = 0
        self.current_bet = 0
    
    def lose_bet(self):
        self.bet = 0
        self.current_bet = 0
        
    def set_bet(self, minimum_bet):
        if not self.isBot:
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
            # Simple bot logic: bet a random amount between minimum and 100
            amount = random.randint(minimum_bet, min(100, self.wallet))
            #amount =50
            self.add_bet(amount)
            print(f"{self.name} (Bot) has placed a bet of {amount}. Remaining funds: {self.wallet}")
    
    def add_to_bet(self, amount):
        if self.add_bet(amount):
            self.current_bet += amount
            print(f"{self.name} has increased their bet by {amount}. Current bet: {self.current_bet}. Remaining funds: {self.wallet}")
        else:
            print(f"{self.name} could not increase their bet by {amount} due to insufficient funds.")

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
        while True:
            player = node.player
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
        for player in players:
            hand=player.hand
            print(f"Evaluating hand for {player.name}: {show_substituted(hand)}")
            check, result= self.check_royal_flush(hand, dealt)
            if check:
                print(f"{player.name} has a Royal Flush!")
                rank=10
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_straight_flush(hand, dealt)
            if check:
                print(f"{player.name} has a Straight Flush!")
                rank=9
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_four_of_a_kind(hand, dealt)
            if check:
                print(f"{player.name} has Four of a Kind!")
                rank=8
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_full_house(hand, dealt)
            if check:
                print(f"{player.name} has a Full House!")
                rank=7
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_flush(hand, dealt)
            if check:
                print(f"{player.name} has a Flush!")
                rank=6
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_straight(hand, dealt)
            if check:
                print(f"{player.name} has a Straight!")
                rank=5
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_three_of_a_kind(hand, dealt)
            if check:
                print(f"{player.name} has Three of a Kind!")
                rank=4
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_two_pair(hand, dealt)
            if check:
                print(f"{player.name} has Two Pair!")
                rank=3
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            check, result= self.check_single_pair(hand, dealt)
            if check:
                print(f"{player.name} has a Pair!")
                rank=2
                if rank>highest_rank:
                    highest_rank=rank
                    winner=player
                    winning_hand=result
                continue
            high_card=self.get_high_card(hand, dealt)
            rank=1
            print(f"{player.name} has High Card: {show_substituted(high_card)}")
            if rank>highest_rank:
                highest_rank=rank
                winner=player
                winning_hand=high_card
        print(f"The winner is {winner.name} with hand: {winning_hand}")

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
