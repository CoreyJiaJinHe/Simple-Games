import sqlite3

class PlayerNotFoundError(Exception):
    def __init__(self, player_name=None, operation=None):
        base_message = "Player not found in database"
        details = []
        if player_name is not None:
            details.append(f"player='{player_name}'")
        if operation is not None:
            details.append(f"operation='{operation}'")
        message = base_message if not details else f"{base_message} ({', '.join(details)})"
        super().__init__(message)

class gameDatabase:
    def __init__(self):
        try:
            self.conn=sqlite3.connect('cardgames.db')
            self.conn.row_factory = sqlite3.Row
            self.cursor=self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            
    def close(self):
        self.conn.close()
    
    
    def initialize_database(self):
        def create_player_table(self):
            self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS players (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            wallet INTEGER, 
                            games_played INTEGER,
                            games_won INTEGER,
                            WINNINGS_TOTAL INTEGER,
                            loans_taken INTEGER DEFAULT 0,
                            debt INTEGER DEFAULT 0
                        )''')
            self.conn.commit()
        def create_game_table(self):
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS games (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    game_type TEXT,
                                    players TEXT,
                                    winner TEXT,
                                    pot INTEGER,
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                )''')
            self.conn.commit()
        create_player_table(self)
        create_game_table(self)
        
    def migrate_player_table(self):
        # Get current columns
        self.cursor.execute("PRAGMA table_info(players);")
        columns = [col[1] for col in self.cursor.fetchall()]

        # Add loans_taken if missing
        if "loans_taken" not in columns:
            print("Adding 'loans_taken' column to players table.")
            self.cursor.execute("ALTER TABLE players ADD COLUMN loans_taken INTEGER DEFAULT 0;")
            self.conn.commit()

        # Add debt if missing
        if "debt" not in columns:
            print("Adding 'debt' column to players table.")
            self.cursor.execute("ALTER TABLE players ADD COLUMN debt INTEGER DEFAULT 0;")
            self.conn.commit()
        
    def debug_show_tables_and_columns(self):
        print("Tables and columns in the database:")
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = self.cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
    
    def debug_clear_tables(self):
        print("Clearing all data from players and games tables.")
        self.cursor.execute("DELETE FROM players;")
        self.cursor.execute("DELETE FROM games;")
        self.conn.commit()

    def debug_get_table_data(self):
        self.cursor.execute("SELECT * FROM players;")
        players=self.cursor.fetchall()
        print("Players Table Data:")
        for player in players:
            print(dict(player))
        
        self.cursor.execute("SELECT * FROM games;")
        games=self.cursor.fetchall()
        print("\nGames Table Data:")
        for game in games:
            print(dict(game))
    
    def debug_get_dev_info(self):
        self.cursor.execute("SELECT * FROM players WHERE username = ?", ("Dev",))
        player = self.cursor.fetchone()
        if player:
            print("Dev's Player Data:")
            print(dict(player))
        else:
            print("Player 'Dev' not found in the players table.")
    
    def get_player(self, username):
        self.cursor.execute('SELECT * FROM players WHERE username=?', (username,))
        player=self.cursor.fetchone()
        if not player:
            raise PlayerNotFoundError(player_name=username, operation="get_player")
        return player
    
    def get_players(self):
        self.cursor.execute('SELECT username FROM players')
        players=self.cursor.fetchall()
        return [player[0] for player in players]

    def add_player(self, username):
        try:
            self.cursor.execute('''INSERT INTO players (username, wallet, games_played, games_won, WINNINGS_TOTAL) 
                    VALUES (?, ?, 0, 0, 0)''', (username, 1000))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Player with username '{username}' already exists.")
    
    def update_player_stats(self, username, wallet_change, won_game, winnings):
        self.cursor.execute('SELECT wallet, games_played, games_won, WINNINGS_TOTAL FROM players WHERE username=?', (username,))
        player=self.cursor.fetchone()
        if player:
            new_wallet=player['wallet'] + wallet_change
            new_games_played=player['games_played'] + 1
            new_games_won=player['games_won'] + (1 if won_game else 0)
            new_winnings_total=player['WINNINGS_TOTAL'] + winnings
            self.cursor.execute('''UPDATE players 
                        SET wallet=?, games_played=?, games_won=?, WINNINGS_TOTAL=? 
                        WHERE username=?''',
                        (new_wallet, new_games_played, new_games_won, new_winnings_total, username))
            self.conn.commit()
        else:
            raise PlayerNotFoundError(player_name=username, operation="update_player_stats")
    
    def update_player_wallet(self, username, amount):
        self.cursor.execute('SELECT wallet FROM players WHERE username=?', (username,))
        player=self.cursor.fetchone()
        if player:
            new_wallet=player['wallet'] + amount
            self.cursor.execute('UPDATE players SET wallet=? WHERE username=?', (new_wallet, username))
            self.conn.commit()
        else:
            raise PlayerNotFoundError(player_name=username, operation="update_player_wallet")
    
    def get_leaderboard(self, limit=10):
        self.cursor.execute('''SELECT username, WINNINGS_TOTAL 
                            FROM players 
                            ORDER BY WINNINGS_TOTAL DESC 
                            LIMIT ?''', (limit,))
        leaderboard=self.cursor.fetchall()
        return leaderboard

    def log_game(self, game_type, players, winner, pot):
        self.cursor.execute('''INSERT INTO games (game_type, players, winner, pot) 
                            VALUES (?, ?, ?, ?)''', 
                            (game_type, players, winner, pot))
        self.conn.commit()
    
    def player_take_loan(self, username, loan_amount=1000):
        self.cursor.execute('UPDATE players SET wallet = wallet + ?, debt = debt + ?, loans_taken = loans_taken +1 WHERE username = ?', 
                            (loan_amount, loan_amount, username))
        self.conn.commit()
    
def __main__():
    db=gameDatabase()
    db.initialize_database()
    db.migrate_player_table()
    db.debug_show_tables_and_columns()
    playerList=db.get_players()
    print(playerList)
    leaderboard=db.get_leaderboard()
    print("\nLeaderboard:")
    for rank, (username, winnings) in enumerate(leaderboard, start=1):
        print(f"{rank}. {username} - Total Winnings: {winnings}")
    #db.debug_get_dev_info()
    #db.debug_get_table_data()
if __name__ == "__main__":
    __main__()