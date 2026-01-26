import sqlite3


class gameDatabase:
    def __init__(self):
        try:
            self.conn=sqlite3.connect('cardgames.db')
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
                            WINNINGS_TOTAL INTEGER
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
            
    
    def get_player(self, username):
        self.cursor.execute('SELECT * FROM players WHERE username=?', (username,))
        player=self.cursor.fetchone()
        if not player:
            print("Player not found in database.")
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
            new_wallet=player[0] + wallet_change
            new_games_played=player[1] + 1
            new_games_won=player[2] + (1 if won_game else 0)
            new_winnings_total=player[3] + winnings
            self.cursor.execute('''UPDATE players 
                        SET wallet=?, games_played=?, games_won=?, WINNINGS_TOTAL=? 
                        WHERE username=?''', 
                        (new_wallet, new_games_played, new_games_won, new_winnings_total, username))
            self.conn.commit()
        else:
            print("Player not found in database.")
    
    def update_player_wallet(self, username, amount):
        self.cursor.execute('SELECT wallet FROM players WHERE username=?', (username,))
        player=self.cursor.fetchone()
        if player:
            new_wallet=player[0] + amount
            self.cursor.execute('UPDATE players SET wallet=? WHERE username=?', (new_wallet, username))
            self.conn.commit()
        else:
            print("Player not found in database.")
    
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
    
def __main__():
    db=gameDatabase()
    db.initialize_database()
