import random

class TicTacToe():
    
    def __init__(self, board_size: int = 3, player_name: str = "Player", count_to_win: int = 3, bot_AI_difficulty: int = 1):
        self.board_size = board_size
        self.board = [[0 for _ in range (board_size)] for _ in range (board_size)]
        self.winner = None
        self.game_over = False
        self.players = [player_name, "Bot"]
        self.bot_AI_difficulty = bot_AI_difficulty # 1 for beginner, 2 for intermediate, 3 for advanced
        
        self.count_to_win = count_to_win
        
    
    def display_board(self):
        for row in self.board:
            display_row = []
            for cell in row:
                if cell == 1:
                    display_row.append("X")
                elif cell == 2:
                    display_row.append("O")
                elif cell == 0:
                    display_row.append("0")
                else:
                    display_row.append(str(cell))
            print(' '.join(display_row))
        print()
    
    
    def beginner_bot_AI(self):
        # Bot's move (for simplicity, it just takes the first available cell)
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    return (i, j)
        #Truthfully it should not reach this point in the first place.
        return None # No moves available, should be a draw
    
    def intermediate_bot_AI(self):
        #Pick at random from the available moves.
        random_moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    random_moves.append((i, j))
        if random_moves:
            return random.choice(random_moves)
        return None # No moves available, should be a draw
        
    def advanced_bot_AI(self):
        #The advanced bot AI will use the minimax algorithm to determine the best move. 
        #It will evaluate the game state and choose the move that maximizes its chances of winning while minimizing the player's chances of winning.
        best_move = None
        best_score = -10**9
        depth_limit = self.suggest_depth_limit()

        for r, c in self.ordered_moves():
            self.board[r][c] = 2
            score = self.minimax(1, -10**9, 10**9, False, depth_limit)
            self.board[r][c] = 0

            if score > best_score:
                best_score = score
                best_move = (r, c)

        return best_move
    
    
    def available_moves(self):
        moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    moves.append((i, j))
        return moves
    
    def is_valid_cell(self, row, col):
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return True
        return False
        
    def has_consecutive_n(self, mark):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]


        #For row
        for r in range(self.board_size):
            #For column
            for c in range(self.board_size):
                #If the cell does not contain the mark we are looking for, skip it and continue to the next cell.
                if self.board[r][c] != mark:
                    continue
                
                #For each direction (right, down, diagonal down-right, diagonal down-left), 
                # we check if there are count_to_win consecutive marks starting from the current cell.
                for dr, dc in directions:
                    end_r = r + (self.count_to_win - 1) * dr
                    end_c = c + (self.count_to_win - 1) * dc
                    if not self.is_valid_cell(end_r, end_c):
                        continue

                    ok = True
                    for k in range(self.count_to_win):
                        nr = r + k * dr
                        nc = c + k * dc
                        if self.board[nr][nc] != mark:
                            ok = False
                            break

                    if ok:
                        return True
        return False
    
    def bot_evaluate_terminal(self, depth):
        #Depth is used to prefer faster wins and slower losses.
        #This function will check if the game has reached a terminal state (win/loss/draw) and 
        # return a score accordingly.
        if self.has_consecutive_n(2):
            return 100000 - depth
        if self.has_consecutive_n(1):
            return -100000 + depth
        if len(self.available_moves()) == 0:
            return 0
        return None
        
    def heuristic_score(self):
        #This function will evaluate the board state and return a heuristic score based on how favorable the position is for the bot. 
        #It will consider factors such as potential winning lines, blocking opponent's winning lines, and controlling the center of the board.
        score = 0
        n = self.board_size
        k = self.count_to_win
        windows = []

        #Generate all possible windows of length k in the board (rows, columns, diagonals) 
        # to evaluate potential winning lines for both the bot and the player.
        #A "window" is a sequence of k cells in a row, column, or diagonal that could potentially lead to a win for either the bot or the player.
        #By evaluating these windows, the bot can assess how favorable the current board state is and make informed decisions about its next move.
        
        #Rows, columns, and diagonals
        #For rows, we iterate through each row and create windows of length k by taking consecutive cells.
        for r in range(n):
            for c in range(n - k + 1):
                windows.append([self.board[r][c + i] for i in range(k)])
        
        #For columns, we iterate through each column and create windows of length k by taking consecutive cells in the vertical direction.
        for c in range(n):
            for r in range(n - k + 1):
                windows.append([self.board[r + i][c] for i in range(k)])
        
        #For diagonals, we create windows of length k by taking consecutive cells in both diagonal directions 
        # (top-left to bottom-right and top-right to bottom-left).
        for r in range(n - k + 1):
            for c in range(n - k + 1):
                windows.append([self.board[r + i][c + i] for i in range(k)])

        for r in range(n - k + 1):
            for c in range(k - 1, n):
                windows.append([self.board[r + i][c - i] for i in range(k)])

        #Evaluate each window and update the score based on the number of bot pieces and player pieces in the window.
        #If a window contains both bot pieces and player pieces, 
        # it is not favorable for either side and can be ignored.
        #If a window contains only bot pieces, it contributes positively to the score, 
        # with more pieces contributing exponentially more.
        #If a window contains only player pieces, it contributes negatively to the score, 
        # with more pieces contributing exponentially more.
        #This heuristic encourages the bot to create and block potential winning lines, 
        # while also considering the strategic value of controlling the center of the board.
        #The exponential scoring helps the bot prioritize moves that lead to winning sooner 
        # and blocking the opponent's winning chances more effectively.
        for w in windows:
            bot = w.count(2)
            player = w.count(1)

            if bot > 0 and player > 0:
                continue

            if bot > 0:
                score += 10 ** bot
            elif player > 0:
                score -= 10 ** player

        return score
    
    def ordered_moves(self):
        #This function will order the available moves based on their heuristic scores. 
        #Moves that are more favorable for the bot will be evaluated first in the minimax algorithm, which can help improve the efficiency of the search.
        center = (self.board_size - 1) / 2.0
        moves = self.available_moves()
        moves.sort(key=lambda m: abs(m[0] - center) + abs(m[1] - center))
        return moves
    
    def suggest_depth_limit(self):
        #This function will suggest a depth limit for the minimax algorithm based on the current state of the board. 
        #As the game progresses and the number of available moves decreases, it may be possible to search deeper in the game tree without exceeding time constraints.
        empties = len(self.available_moves())

        if self.board_size == 3 and self.count_to_win == 3:
            return empties
        if self.board_size <= 4:
            return min(5, empties)
        if self.board_size <= 5:
            return min(4, empties)
        return min(3, empties)
    
    def minimax(self, depth, alpha, beta, maximizing, depth_limit):
        #This function will implement the minimax algorithm with alpha-beta pruning. 
        #It will recursively evaluate the game tree and return the best move for the bot based on the current board state and the specified depth limit.
        terminal = self.bot_evaluate_terminal(depth)
        if terminal is not None:
            return terminal

        if depth >= depth_limit:
            return self.heuristic_score()

        #If maximizing is True, the bot is trying to maximize its score, 
        # so it will look for the move that gives the highest score.
        #If maximizing is False, the bot is simulating the opponent's move, 
        # which tries to minimize the bot's score, so it will look for the move that gives the lowest score.
        #Alpha-beta pruning is used to skip evaluating branches of the game tree that won't affect the final decision, 
        # which can significantly reduce the number of nodes evaluated and improve the efficiency of the algorithm.
        if maximizing:
            best = -10**9
            for r, c in self.ordered_moves():
                self.board[r][c] = 2
                val = self.minimax(depth + 1, alpha, beta, False, depth_limit)
                self.board[r][c] = 0

                if val > best:
                    #If the current move's score is better than the best score found so far for the maximizing player,
                    #update the best score.
                    best = val
                if best > alpha:
                    #If the current best score is better than the best score found so far for the maximizing player,
                    # update alpha.
                    alpha = best
                if beta <= alpha:
                    #Prune the remaining branches since they won't affect the final decision.
                    break
            return best

        #Minimizing player's turn
        best = 10**9
        for r, c in self.ordered_moves():
            self.board[r][c] = 1
            val = self.minimax(depth + 1, alpha, beta, True, depth_limit)
            self.board[r][c] = 0

            if val < best:
                best = val
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best
    
        
    
    def begin_game(self):
        current_player = self.players[0]
        while not self.game_over:
            self.display_board()
            if current_player == self.players[0]:
                #While the move is invalid, or the game has not ended, keep asking for input
                valid_move = False
                while not valid_move:
                    row = int(input("Enter row (0-indexed): "))
                    col = int(input("Enter column (0-indexed): "))
                    valid_move = self.make_move(current_player, row, col)
                    print(valid_move)
            else:
                move = None
                if self.bot_AI_difficulty == 1:
                    move = self.beginner_bot_AI()
                elif self.bot_AI_difficulty == 2:
                    move = self.intermediate_bot_AI()
                else:
                    move = self.advanced_bot_AI()

                if move is not None:
                    i, j = move
                    self.make_move(current_player, i, j)
                else:
                    self.game_over = True
                    print("It's a draw!")
            current_player = self.players[1] if current_player == self.players[0] else self.players[0]
        self.display_board()
    
    def make_move(self, player, row: int, col: int):
        if not self.is_valid_cell(row, col):
            print("Move out of bounds.")
            return False
        
        if self.game_over:
            print("Game is already over.")
            return False
        
        if self.board[row][col] != 0:
            print("Cell is already occupied.")
            return False
        
        
        if player == self.players[0]:
            self.board[row][col] = 1
        else:
            self.board[row][col] = 2
        
        if self.check_winner_consecutive(player):
            print(f"{player} wins!")
        elif all(cell != 0 for row in self.board for cell in row):
            self.game_over = True
            print("It's a draw!")
        
        return True #Game continues
    
    def check_winner_consecutive(self, player):
        if player == self.players[0]:
            mark = 1
        else:
            mark = 2

        if self.has_consecutive_n(mark):
            self.winner = mark
            self.game_over = True
            return True
        return False
    


if "__main__" == __name__:
    game = TicTacToe(board_size=5, player_name="Player", count_to_win=3, bot_AI_difficulty=3)
    game.begin_game()
    