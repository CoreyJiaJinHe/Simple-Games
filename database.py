import sqlite3

def initialize_database():
    conn=sqlite3.connect('cardgames.db')
    cursor=conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS players (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT UNIQUE,
                       wallet INTEGER
                       games_played INTEGER,
                       games_won INTEGER,
                       WINNINGS_TOTAL INTEGER
                   )''')
    
    conn.commit()
    conn.close()
    
###initialize_database()
class gameDatabase:
    def __init__(self):
        self.conn=sqlite3.connect('cardgames.db')
        self.cursor=self.conn.cursor()
    
    def close(self):
        self.conn.close()
    
    
    def get_player(self, username):
        self.cursor.execute('SELECT * FROM players WHERE username=?', (username,))
        player=self.cursor.fetchone()
        return player

    def add_player(self, username):
        self.cursor.execute('''INSERT INTO players (username, wallet, games_played, games_won, WINNINGS_TOTAL) 
                    VALUES (?, ?, 0, 0, 0)''', (username, 1000))
        self.conn.commit()
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
    
    def get_leaderboard(self, limit=10):
        self.cursor.execute('''SELECT username, WINNINGS_TOTAL 
                            FROM players 
                            ORDER BY WINNINGS_TOTAL DESC 
                            LIMIT ?''', (limit,))
        leaderboard=self.cursor.fetchall()
        return leaderboard

