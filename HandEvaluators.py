
from utils import remove_suit, custom_sort, rank

class PokerHandEvaluator():
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

class BlackjackHandEvaluator():
    def evaluate_hand(self, hand):
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                  '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
        total = 0
        aces = 0
        
        for card in hand:
            rank = card[:-1]  # Remove suit
            total += values[rank]
            if rank == 'A':
                aces += 1
        
        # Adjust for aces
        while total > 21 and aces:
            total -= 10
            aces -= 1
        
        if total == 21 and len(hand) == 2:
            return "Blackjack", total
        elif total > 21:
            return "Bust", total
        else:
            return "Continue", total