
from utils import remove_suit_hand, custom_sort, rank

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
        
    def check_straight_flush(self, hand, dealt):
        # Check straight within each suit separately
        combined = hand.copy() + dealt.copy()
        suits = ["H", "D", "C", "S"]
        for s in suits:
            suited = [c for c in combined if c[-1] == s]
            suited_ranks = [c[:-1] for c in suited]
            found, straight_ranks = self._find_straight_ranks(suited_ranks)
            if found:
                return True, [r + s for r in straight_ranks]
        return False, []
    
    def check_straight(self, hand, dealt):
        combined = hand.copy() + dealt.copy()
        ranks_only = [c[:-1] for c in combined]
        found, straight_ranks = self._find_straight_ranks(ranks_only)
        if found:
            return True, straight_ranks
        return False, []

    def _find_straight_ranks(self, ranks):
        """Return (True, [r1..r5]) for highest straight found in ranks.
        Handles Ace-high (A=14) and Ace-low wheel (A=1 with 2-3-4-5)."""
        if not ranks:
            return False, []
        # Map ranks to numeric values (Ace high=14)
        value_map = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
                     "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        # Helper to check consecutive windows
        def find_consecutive(vals):
            vals = sorted(set(vals))
            best = None
            for i in range(len(vals) - 4):
                window = vals[i:i+5]
                if all(window[j] == window[0] + j for j in range(5)):
                    if best is None or window[-1] > best[-1]:
                        best = window
            return best
        # Try Ace-high first
        values_high = [value_map.get(r, 0) for r in ranks]
        best_high = find_consecutive(values_high)
        if best_high:
            # Convert back to rank strings
            inv_map = {v: k for k, v in value_map.items()}
            return True, [inv_map[v] for v in best_high]
        # Try Ace-low (wheel): treat Ace as 1
        values_low = [1 if r == "A" else value_map.get(r, 0) for r in ranks]
        best_low = find_consecutive(values_low)
        if best_low and best_low[-1] == 5:
            inv_map_low = {1: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
                           8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"}
            return True, [inv_map_low[v] for v in best_low]
        return False, []
    
    def check_four_of_a_kind(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        temp_hand_ranks=remove_suit_hand(temp_hand)
        for card_rank in rank:
            if temp_hand_ranks.count(card_rank)==4:
                # Collect the actual cards with suits
                four_cards = [c for c in temp_hand if c[:-1] == card_rank]
                return True, four_cards
        return False, []
    
    def check_three_of_a_kind(self,hand,dealt):
        temp_hand=hand.copy() + dealt.copy()
        temp_hand_ranks=remove_suit_hand(temp_hand)
        for card_rank in rank:
            if temp_hand_ranks.count(card_rank)==3:
                three_cards = [c for c in temp_hand if c[:-1] == card_rank]
                return True, three_cards
        return False, []
    
    def check_single_pair(self,hand,dealt):
        
        temp_hand=hand.copy() + dealt.copy()
        temp_hand_ranks=remove_suit_hand(temp_hand)
        for card_rank in rank:
            if temp_hand_ranks.count(card_rank) == 2:
                pair_cards = [c for c in temp_hand if c[:-1] == card_rank]
                return True, pair_cards
        return False, []
    
    def check_two_pair(self,hand,dealt):
        temp_hand = hand.copy() + dealt.copy()
        temp_hand_ranks = remove_suit_hand(temp_hand)
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
    
    def remove_suit_card(self, card):
        return card[:-1]
    
    def get_highest_rank(self, hand):
        temp_hand = hand.copy()
        temp_hand = custom_sort(temp_hand)
        return temp_hand[-1][:-1]
    def get_highest_suit(self, hand):
        temp_hand = hand.copy()
        temp_hand = custom_sort(temp_hand)
        return temp_hand[-1][-1]

    def get_total(self, hand):
        total = 0
        for card in hand:
            card = card[:-1]
            total = total + rank.index(card)+1
        return total
    
    def sort_hand(self, hand):
        temp_hand = hand.copy()
        temp_hand = custom_sort(temp_hand)
        return temp_hand

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
        
        # if total == 21 and len(hand) == 2:
        #     return total
        # elif total > 21:
        #     return total
        # else:
        return total

    def is_blackjack(self, hand):
        status = self.evaluate_hand(hand)
        #print (f"Evaluating hand: {hand}, Total value: {status}, Length: {len(hand)}")
        if (status == 21 and len(hand) == 2):
            return True
        return False
    
    def is_bust(self, hand):
        status = self.evaluate_hand(hand)
        return status > 21