
import random

suit=["H", "D", "C", "S"]
cards=[]
rank = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
substitute=["1","11","12","13"]

for y in suit:
    for x in range (1, 14):
        # if (x==1):
        #     cards.append("A"+y)
        # elif (x==11):
        #     cards.append("J"+y)
        # elif (x==12):
        #     cards.append("Q"+y)
        # elif (x==13):
        #     cards.append("K"+y)
        # else:
            cards.append(str(x)+y)
        
print (cards)

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
    substituted_hand=[]
    for card in hand:
        if card[:-1]=="1":
            substituted_hand.append("A"+card[-1])
        elif card[:-1]=="11":
            substituted_hand.append("J"+card[-1])
        elif card[:-1]=="12":
            substituted_hand.append("Q"+card[-1])
        elif card[:-1]=="13":
            substituted_hand.append("K"+card[-1])
        else:
            substituted_hand.append(card)
    return substituted_hand
    
    
#print(custom_sort(["3H", "AS", "10D", "KC", "5S"]))
    

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
    
class Player():
    def __init__(self,name):
        self.name=name
        self.hand=[]
        
    def request_card(self, dealer):
        card = dealer.deal_card()
        self.hand.append(card)
        
class Poker():
    def __init__ (self, player_names):
        self.dealer = Dealer()
        self.players = [Player(name) for name in player_names]
        self.dealt=[]
        
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
    

    def game_phases(self):
        self.deal_initial_hands()
        self.show_hands()
        
        flop = self.deal_flop()
        print(f"Flop: {show_substituted(flop)}")
        self.dealt = flop.copy()
        turn = self.deal_turn()
        print(f"Turn: {show_substituted([turn])}")
        self.dealt = self.dealt + [turn]
        
        river = self.deal_river()
        print(f"River: {show_substituted([river])}")
        
        self.dealt = self.dealt + [river]
        print(f"Dealt cards: {show_substituted(self.dealt)}")
        
        self.show_hands()
        self.determine_winner(self.players, self.dealt)
    
        
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
            
            
            
            # if self.check_royal_flush(hand, dealt)[0]:
            #     
            # elif self.check_straight_flush(hand, dealt)[0]:
            #     print(f"{player.name} has a Straight Flush!")
            # elif self.check_four_of_a_kind(hand, dealt)[0]:
            #     print(f"{player.name} has Four of a Kind!")
            # elif self.check_full_house(hand, dealt)[0]:
            #     print(f"{player.name} has a Full House!")
            # elif self.check_flush(hand, dealt)[0]:
            #     print(f"{player.name} has a Flush!")
            # elif self.check_straight(hand, dealt)[0]:
            #     print(f"{player.name} has a Straight!")
            # elif self.check_three_of_a_kind(hand, dealt)[0]:
            #     print(f"{player.name} has Three of a Kind!")
            # elif self.check_two_pair(hand, dealt)[0]:
            #     print(f"{player.name} has Two Pair!")
            # elif self.check_single_pair(hand, dealt)[0]:
            #     print(f"{player.name} has a Pair!")
            # else:
            #     high_card=self.get_high_card(hand, dealt)
            #     print(f"{player.name} has High Card: {high_card}")
            
        
            
        
        
        
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
        temp_hand=remove_suit(temp_hand)
        for card in rank:
            if temp_hand.count(card)==4:
                return True, card
        return False, []
    
    def check_three_of_a_kind(self,hand,dealt):
        
        temp_hand=hand.copy() + dealt.copy()
        temp_hand=remove_suit(temp_hand)
        for card in rank:
            if temp_hand.count(card)==3:
                return True, card
        return False, []
    
    def check_single_pair(self,hand,dealt):
        
        temp_hand=hand.copy() + dealt.copy()
        temp_hand=remove_suit(temp_hand)
        pairs=[]
        for card in rank:
            if temp_hand.count(card)==2:
                pairs.append(card)
                return True, pairs
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
    

x = Poker(["Alice", "Bob"])
x.game_phases()




# hand=["3H", "4D", "5S", "6C",  "9D", "JH", "7H",]
# print(x.check_straight(hand, []))