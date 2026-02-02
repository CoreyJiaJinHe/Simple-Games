from HandEvaluators import PokerHandEvaluator, BlackjackHandEvaluator
class HandEvaluatorFactory():
    @staticmethod
    def get_evaluator(game_type):
        if game_type == "Poker":
            return PokerHandEvaluator()
        elif game_type == "Blackjack":
            return BlackjackHandEvaluator()
        # Additional game types can be added here
        raise ValueError(f"Unsupported game type: {game_type}")
    