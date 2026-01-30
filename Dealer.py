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
    
    def show_hand(self):
        return self.hand
    
    def debug_deck(self):
        print(self.deck)
        print(self.used_cards)