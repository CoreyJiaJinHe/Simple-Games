
import database
class Database_Helper():
    detailed_debug_print_override = False
    def requires_player(func):
        def wrapper(self, player_name, *args, **kwargs):
            if player_name in self.players:
                return func(self, player_name, *args, **kwargs)
            else:
                return None
        return wrapper

    def __init__(self):
        self.db = database.gameDatabase()
        self.players =self.retrieve_list_of_players()
    def log_game(self, game_type, players, winner, pot):
        if self.detailed_debug_print_override:
            print("Logging game to database...")
            print(f"{game_type}, {players}, {winner}, {pot}")
        self.db.log_game(game_type, players, winner, pot)
        print(f"{game_type} Game logged to database.")
    
    
    @requires_player
    def retrieve_player_wallet(self, player_name):
        player = self.db.get_player(player_name)
        return player['wallet'] if player else None
    
    def retrieve_list_of_players(self):
        return self.db.get_players()
    
    def add_player(self, player_name):
        self.db.add_player(player_name)
        print(f"Player {player_name} added to database.")
    
    
    @requires_player
    def update_player_stats(self, player_name, wallet_change, won_game, winnings):
        if self.detailed_debug_print_override:
            print(f"Updating stats for {player_name}: wallet_change={wallet_change}, won_game={won_game}, winnings={winnings}")
        self.db.update_player_stats(player_name, wallet_change, won_game, winnings)

    @requires_player
    def update_player_wallet(self, player_name, amount):
        self.db.update_player_wallet(player_name, amount)

    @requires_player
    def player_take_loan(self, player_name):
        self.db.player_take_loan(player_name)

    @requires_player
    def get_player_debt(self, player_name):
        player = self.db.get_player(player_name)
        return player['debt'] if player else None
    
# x = Database_Helper()
# x.add_player("Dev")
# x.retrieve_player_wallet("Dev")