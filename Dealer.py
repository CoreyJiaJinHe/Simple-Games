import random
import utils

class Dealer():
    def __init__(self):
        deck = utils.init_deck()
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