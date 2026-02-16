import random
import utils

class Dealer():
    def __init__(self):
        deck = utils.init_deck()
        random.shuffle(deck)
        self.deck = deck
        self.hand=[]
        self.used_cards=[]
    def deal_card(self):
        card = self.deck.pop()
        self.used_cards.append(card)
        return card
    
    def deal_self(self):
        card = self.deal_card()
        self.used_cards.append(card)
        self.hand.append(card)
    
    def deal_self_return(self):
        card = self.deal_card()
        self.used_cards.append(card)
        self.hand.append(card)
        return card
    
    def get_hand(self):
        return self.hand
    
    def discard_card(self, card_index):
        if 0 <= card_index < len(self.hand):
            card = self.hand.pop(card_index)
            self.used_cards.append(card)
        else:
            print(f"Invalid card index. Please choose a number between 0 and {len(self.hand)-1}.")
    def store_used_card(self, card):
        self.used_cards.append(card)
    
    def debug_deck(self):
        print(self.deck)
        print(self.used_cards)