
import random

from HandEvaluators import PokerHandEvaluator
from HandEvaluatorFactory import HandEvaluatorFactory
class Player():
    def __init__(self,name, wallet=1000, bet_callback=None):
        self.name=name
        self.hand=[]
        self.table=[]
        self.wallet=wallet
        self.bet=0
        self.current_bet=0
        self.isBot=False
        self.risk_tolerance=random.choice(["low","medium","high"])
        self.isFolded=False
        self.bet_callback = bet_callback
            
        
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
    def __init__(self, name, wallet=1000, game_type="Poker"):
        super().__init__(name, wallet)
        self.isBot = True
        self.game_type=game_type
        self.risk_tolerance = random.choice(["low", "medium", "high"])
        self.evaluator=None
        if self.isBot:
            self.evaluator = HandEvaluatorFactory.get_evaluator(self.game_type)
        
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
        rank, result, name = self.evaluator.evaluate_hand(hand, dealt)
        print (f"{self.name} (Bot) assesses its hand as a {name}.")
        if rank >= 7:  # Full House or better
            return 3.0
        elif rank >= 4:  # Three of a Kind to Straight
            return 1.5
        elif rank >= 2:  # Pair to Two Pair
            return 1
        else:  # High Card
            return 0.5
    