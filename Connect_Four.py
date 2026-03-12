



class PlayerNode:
    def __init__(self, player):
        self.player = player
        self.next = None
        self.prev = None
    
    def add_player(self, new_player):
        new_node = PlayerNode(new_player)
        if self.next is None:  # First player being added
            self.next = new_node
            self.prev = new_node
            new_node.next = self
            new_node.prev = self
        else:
            new_node.prev = self.prev
            new_node.next = self
            self.prev.next = new_node
            self.prev = new_node
            
class ConnectFour():
    
    def __init__(self, player_names):
        self.board = [[0 for i in range(7)] for j in range(6)]
        user_player = player_names[0]
        bot_player= player_names[1]
        self.players = [user_player, bot_player]
        
        
        self.player_nodes = [PlayerNode(p) for p in self.players]
        n = len(self.player_nodes)
        for i in range(n):
            self.player_nodes[i].next = self.player_nodes[(i+1)%n]
            self.player_nodes[i].prev = self.player_nodes[(i-1)%n]
        
        self.winner = None
        self.game_over = False
    
    def display_board(self):
        first_player = self.players[0] if len(self.players) > 0 else None
        second_player = self.players[1] if len(self.players) > 1 else None

        for row in self.board:
            display_row = []
            for cell in row:
                if cell == first_player:
                    display_row.append("X")
                elif cell == second_player:
                    display_row.append("B")
                elif cell == 0:
                    display_row.append("0")
                else:
                    display_row.append(str(cell))
            print(' '.join(display_row))
        print()
    
    def game_loop(self):
        current_player_node = self.player_nodes[0]
        while not self.game_over:
            self.display_board()
            player = current_player_node.player
            print(f"{player}'s turn.")
            column = int(input("Enter the column (0-6) to drop your piece: "))
            self.make_move(player, column)
            current_player_node = current_player_node.next
        
        self.display_board()
        if self.winner is not None:
            print(f"Congratulations! {self.winner} wins!")
        else:
            print("It's a draw!")
    
    def make_move(self, player, column):
        if self.game_over:
            print("Game is already over. Please start a new game.")
            return
        
        if column < 0 or column > 6:
            print("Invalid column. Please choose a column between 0 and 6.")
            return
        
        for i in range(5, -1, -1):
            if self.board[i][column] == 0:
                self.board[i][column] = player
                self.determine_winner()
                return
        
        print("Column is full. Please choose a different column.")
    
    def determine_winner(self):
        # Check the board state and determine if there is a winner.
        for i in range(6):
            for j in range(7):
                if self.board[i][j] != 0:
                    player = self.board[i][j]
                    # Check horizontal
                    if j <= 3 and all(self.board[i][k] == player for k in range(j, j + 4)):
                        self.winner = player
                        self.game_over = True
                        return
                    # Check vertical
                    if i <= 2 and all(self.board[k][j] == player for k in range(i, i + 4)):
                        self.winner = player
                        self.game_over = True
                        return
                    # Check diagonal (bottom-left to top-right)
                    if i >= 3 and j <= 3 and all(self.board[i - k][j + k] == player for k in range(4)):
                        self.winner = player
                        self.game_over = True
                        return
                    # Check diagonal (top-left to bottom-right)
                    if i <= 2 and j <= 3 and all(self.board[i + k][j + k] == player for k in range(4)):
                        self.winner = player
                        self.game_over = True
                        return
        
        # Check for a draw
        if all(self.board[i][j] != 0 for i in range(6) for j in range(7)):
            self.winner = None
            self.game_over = True
            return
    
        
        
        
if __name__ == "__main__":
    player_names = ["Player1", "Bot1", "Bot2"]
    game = ConnectFour(player_names)
    game.game_loop()