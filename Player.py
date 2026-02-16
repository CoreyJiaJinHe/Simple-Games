
import random

from Dealer import Dealer
from HandEvaluators import PokerHandEvaluator
from HandEvaluatorFactory import HandEvaluatorFactory
class Player():
    def __init__(self,name, wallet=1000, action_callback=None):
        self.name=name
        self.hand=[]
        self.hands=[] #For split hands in blackjack
        self.bets=[] #For split hands in blackjack
        self.table=[]
        self.wallet=wallet
        self.bet=0
        self.current_bet=0
        self.isBot=False
        self.risk_tolerance=random.choice(["low","medium","high"])
        self.isFolded=False
        self.action_callback = action_callback
            
        
    def request_card(self, dealer : Dealer):
        card = dealer.deal_card()
        self.hand.append(card)
    
    def discard_card(self, dealer : Dealer, card_index):
        if not self.hand:
            print(f"{self.name} has no cards to discard.")
            return
        
        if 0 <= card_index < len(self.hand):
            discarded_card = self.hand.pop(card_index)
            dealer.store_used_card(discarded_card)
            print(f"{self.name} has discarded {discarded_card}.")
        else:
            print(f"Invalid card index. Please choose a number between 0 and {len(self.hand)-1}.")
    
    def return_bet(self):
        self.wallet += self.bet
        #print(f"{self.name} has returned their bet of {self.bet}. New wallet balance: {self.wallet}")
        self.reset()
    
    def surrender_bet(self,refund):
        self.wallet += refund
        #print(f"{self.name} has surrendered. {refund} has been returned. New wallet balance: {self.wallet}")
        self.reset()
    
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
        if self.action_callback:
            self.action_callback(self, minimum_bet)
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
    def __init__(self, name, wallet=1000, game_type="Poker"):
        super().__init__(name, wallet)
        self.isBot = True
        self.game_type=game_type
        self.risk_tolerance = random.choice(["low", "medium", "high"])
        self.evaluator=None
        #self.maximum_bet = 0
        if self.isBot:
            self.evaluator = HandEvaluatorFactory.get_evaluator(self.game_type)
        