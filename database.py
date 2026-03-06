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

    def get_game_logs(self, game_type_filter=None):
        query = 'SELECT id, game_type, players, winner, pot, timestamp FROM games'
        params = []
        if game_type_filter:
            query += ' WHERE game_type LIKE ?'
            params.append(f'%{game_type_filter}%')
        query += ' ORDER BY timestamp ASC, id ASC'
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

    def get_player_financials(self):
        self.cursor.execute('SELECT username, wallet, WINNINGS_TOTAL FROM players')
        return self.cursor.fetchall()

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


class DatabaseVisualizer:
    def __init__(self, database):
        self.database = database

    @staticmethod
    def _split_name_list(value):
        if value is None:
            return []
        return [name.strip() for name in str(value).split(',') if name and name.strip()]

    @staticmethod
    def _is_bot_name(name):
        lowered = name.strip().lower()
        return lowered.startswith('bot')

    @staticmethod
    def _autopct_with_counts(values):
        total = sum(values)

        def formatter(pct):
            if total <= 0:
                return ""
            count = int(round((pct / 100.0) * total))
            return f"{count} ({pct:.1f}%)"

        return formatter

    def _fetch_game_logs(self, game_type_filter=None):
        return self.database.get_game_logs(game_type_filter=game_type_filter)

    def _collect_known_names(self):
        known_names = set()

        try:
            for db_player_name in self.database.get_players():
                if db_player_name:
                    known_names.add(db_player_name)
        except Exception:
            pass

        for game_log in self._fetch_game_logs():
            known_names.update(self._split_name_list(game_log['players']))
            known_names.update(self._split_name_list(game_log['winner']))

        return sorted((name for name in known_names if name), key=str.lower)

    def _collect_known_bots(self):
        return [name for name in self._collect_known_names() if self._is_bot_name(name)]

    def get_selectable_players(self):
        all_known_names = self._collect_known_names()
        human_players = [name for name in all_known_names if not self._is_bot_name(name)]
        return human_players if human_players else all_known_names

    def get_player_dashboard_data(self, player_name, game_type_filter=None):
        game_logs = self._fetch_game_logs(game_type_filter=game_type_filter)

        game_counts_by_type = {}
        losses_by_bot_name = {}
        total_games_played = 0
        wins_count = 0
        losses_count = 0

        for game_log in game_logs:
            participant_names = self._split_name_list(game_log['players'])
            if player_name not in participant_names:
                continue

            winner_names = self._split_name_list(game_log['winner'])
            game_type_name = (game_log['game_type'] or 'Unknown').strip() or 'Unknown'

            total_games_played += 1
            game_counts_by_type[game_type_name] = game_counts_by_type.get(game_type_name, 0) + 1

            if player_name in winner_names:
                wins_count += 1
                continue

            losses_count += 1
            for winner_name in winner_names:
                if winner_name != player_name and self._is_bot_name(winner_name):
                    losses_by_bot_name[winner_name] = losses_by_bot_name.get(winner_name, 0) + 1

        sorted_game_type_items = sorted(game_counts_by_type.items(), key=lambda item: (-item[1], item[0].lower()))

        return {
            'player': player_name,
            'total_games': total_games_played,
            'wins': wins_count,
            'losses': losses_count,
            'game_type_labels': [label for label, _ in sorted_game_type_items],
            'game_type_values': [value for _, value in sorted_game_type_items],
            'losses_by_bot': losses_by_bot_name,
        }

    def _build_participant_summary(self, game_type_filter=None):
        game_logs = self._fetch_game_logs(game_type_filter=game_type_filter)
        participant_summary = {}

        for game_log in game_logs:
            participant_names = self._split_name_list(game_log['players'])
            winner_names = self._split_name_list(game_log['winner'])

            if participant_names:
                winner_set = {winner_name for winner_name in winner_names if winner_name in participant_names}
                if not winner_set:
                    winner_set = set(winner_names)
            else:
                winner_set = set(winner_names)

            for participant_name in participant_names:
                participant_stats = participant_summary.setdefault(participant_name, {'games': 0, 'wins': 0, 'losses': 0})
                participant_stats['games'] += 1

            for winner_name in winner_set:
                winner_stats = participant_summary.setdefault(winner_name, {'games': 0, 'wins': 0, 'losses': 0})
                winner_stats['wins'] += 1

        for participant_stats in participant_summary.values():
            participant_stats['losses'] = max(0, participant_stats['games'] - participant_stats['wins'])

        return participant_summary

    def _fetch_player_financials(self):
        financial_rows = self.database.get_player_financials()
        financials_by_player = {}
        for financial_row in financial_rows:
            financials_by_player[financial_row['username']] = {
                'wallet': financial_row['wallet'],
                'winnings_total': financial_row['WINNINGS_TOTAL'],
            }
        return financials_by_player

    def get_player_summary_table(self, game_type_filter=None):
        participant_summary = self._build_participant_summary(game_type_filter=game_type_filter)
        financials_by_player = self._fetch_player_financials()

        all_player_names = set(participant_summary.keys()) | set(financials_by_player.keys())
        summary_rows = []
        for player_name in all_player_names:
            player_stats = participant_summary.get(player_name, {'games': 0, 'wins': 0, 'losses': 0})
            player_financials = financials_by_player.get(player_name, {})
            games_played = player_stats['games']
            games_won = player_stats['wins']
            games_lost = player_stats['losses']
            win_rate = (games_won / games_played * 100.0) if games_played else 0.0
            summary_rows.append({
                'player': player_name,
                'wallet': player_financials.get('wallet', '-'),
                'winnings_total': player_financials.get('winnings_total', '-'),
                'games': games_played,
                'wins': games_won,
                'losses': games_lost,
                'win_rate': round(win_rate, 1),
            })

        # Keep human players first and bots last, then sort by activity within each group.
        summary_rows.sort(
            key=lambda row: (
                self._is_bot_name(row['player']),
                -row['games'],
                -row['wins'],
                row['player'].lower(),
            )
        )
        return summary_rows

    def _draw_game_type_distribution(self, figure, player_name, game_type_filter=None):
        figure.clear()
        axis = figure.add_subplot(111)
        player_data = self.get_player_dashboard_data(player_name, game_type_filter=game_type_filter)

        game_type_values = [int(value) for value in player_data['game_type_values'] if int(value) > 0]
        game_type_labels = [str(label) for label in player_data['game_type_labels']]

        try:
            if game_type_values and sum(game_type_values) > 0:
                # One-slice pies are rendered via a dedicated branch to avoid edge-case
                # failures in some matplotlib versions when autopct is used.
                if len(game_type_values) == 1:
                    only_value = game_type_values[0]
                    only_label = game_type_labels[0] if game_type_labels else 'Game Type'
                    axis.pie(
                        [1],
                        labels=[only_label],
                        startangle=90,
                        colors=['#5b8ff9'],
                        wedgeprops={'edgecolor': 'white'}
                    )
                    axis.text(0, 0, f'{only_value} (100.0%)', ha='center', va='center', fontsize=10)
                else:
                    axis.pie(
                        game_type_values,
                        labels=game_type_labels,
                        autopct=self._autopct_with_counts(game_type_values),
                        startangle=130,
                        wedgeprops={'edgecolor': 'white'}
                    )
            else:
                axis.pie(
                    [1],
                    labels=['No Games'],
                    colors=['#cfd8dc'],
                    startangle=90,
                    wedgeprops={'edgecolor': 'white'}
                )
                axis.text(0, 0, '0 games', ha='center', va='center', fontsize=10)
        except Exception:
            # Last-resort fallback keeps the panel stable instead of crashing the UI.
            axis.clear()
            axis.pie(
                [1],
                labels=['Unavailable'],
                colors=['#cfd8dc'],
                startangle=90,
                wedgeprops={'edgecolor': 'white'}
            )
            axis.text(0, 0, 'Could not render', ha='center', va='center', fontsize=10)

        axis.set_title('Game Type Distribution')
        axis.axis('equal')
        figure.tight_layout()

    def _draw_wins_losses(self, figure, player_name, game_type_filter=None):
        figure.clear()
        axis = figure.add_subplot(111)
        player_data = self.get_player_dashboard_data(player_name, game_type_filter=game_type_filter)

        wins_count = player_data['wins']
        losses_count = player_data['losses']
        total_games_played = player_data['total_games']

        if total_games_played > 0:
            pie_values = [wins_count, losses_count]
            pie_labels = [f'Wins ({wins_count})', f'Losses ({losses_count})']
            axis.pie(
                pie_values,
                labels=pie_labels,
                autopct=self._autopct_with_counts(pie_values),
                startangle=90,
                colors=['#2a9d8f', '#e76f51'],
                wedgeprops={'edgecolor': 'white'}
            )
        else:
            axis.pie(
                [1],
                labels=['No Games'],
                colors=['#cfd8dc'],
                startangle=90,
                wedgeprops={'edgecolor': 'white'}
            )
            axis.text(0, 0, '0 wins / 0 losses', ha='center', va='center', fontsize=10)

        axis.set_title(f'Wins vs Losses (Total Games: {total_games_played})')
        axis.axis('equal')
        figure.tight_layout()

    def _draw_losses_by_bot(self, figure, player_name, game_type_filter=None):
        figure.clear()
        axis = figure.add_subplot(111)
        player_data = self.get_player_dashboard_data(player_name, game_type_filter=game_type_filter)

        known_bot_names = self._collect_known_bots()
        losses_by_bot_name = player_data['losses_by_bot']

        if known_bot_names:
            bot_labels = known_bot_names
            bot_loss_values = [losses_by_bot_name.get(bot_name, 0) for bot_name in known_bot_names]
        else:
            bot_labels = ['No Bots']
            bot_loss_values = [0]

        bars = axis.bar(bot_labels, bot_loss_values, color='#457b9d')
        axis.set_ylabel('Losses')
        axis.set_title('Losses by Bot')
        axis.set_axisbelow(True)
        axis.grid(axis='y', alpha=0.25)
        axis.tick_params(axis='x', rotation=20)

        max_loss_value = max(bot_loss_values) if bot_loss_values else 0
        axis.set_ylim(0, max(1, max_loss_value + 1))

        for bar, loss_value in zip(bars, bot_loss_values):
            axis.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.05,
                str(loss_value),
                ha='center',
                va='bottom'
            )

        if sum(bot_loss_values) == 0:
            axis.text(0.5, 0.92, f'No bot losses for {player_name}', transform=axis.transAxes, ha='center', va='center')

        figure.tight_layout()

    def _build_summary_table_widget(self, game_type_filter=None):
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

        summary_rows = self.get_player_summary_table(game_type_filter=game_type_filter)
        summary_table = QTableWidget()
        summary_table.setColumnCount(7)
        summary_table.setHorizontalHeaderLabels(['Player', 'Wallet', 'Winnings Total', 'Games', 'Wins', 'Losses', 'Win %'])
        summary_table.setRowCount(len(summary_rows))
        summary_table.setAlternatingRowColors(True)
        summary_table.setSortingEnabled(False)

        for row_index, summary_row in enumerate(summary_rows):
            summary_table.setItem(row_index, 0, QTableWidgetItem(str(summary_row['player'])))
            summary_table.setItem(row_index, 1, QTableWidgetItem(str(summary_row['wallet'])))
            summary_table.setItem(row_index, 2, QTableWidgetItem(str(summary_row['winnings_total'])))
            summary_table.setItem(row_index, 3, QTableWidgetItem(str(summary_row['games'])))
            summary_table.setItem(row_index, 4, QTableWidgetItem(str(summary_row['wins'])))
            summary_table.setItem(row_index, 5, QTableWidgetItem(str(summary_row['losses'])))
            summary_table.setItem(row_index, 6, QTableWidgetItem(str(summary_row['win_rate'])))

        header = summary_table.horizontalHeader()
        header.setStretchLastSection(True)
        summary_table.resizeColumnsToContents()
        return summary_table

    def show_data_visualizer(self, save_path=None, show=True, game_type_filter=None):
        selectable_players = self.get_selectable_players()
        if not selectable_players:
            print('No players available for visualization.')
            return None

        try:
            import sys
            from PyQt5.QtWidgets import (
                QApplication,
                QComboBox,
                QGridLayout,
                QGroupBox,
                QHBoxLayout,
                QLabel,
                QVBoxLayout,
                QWidget,
            )
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
        except ImportError as exc:
            print(f'Visualizer dependencies missing: {exc}')
            print('Install requirements with: pip install PyQt5 matplotlib')
            return None

        if not show:
            figure = Figure(figsize=(14, 10))
            self._draw_game_type_distribution(figure, selectable_players[0], game_type_filter=game_type_filter)
            if save_path:
                figure.savefig(save_path, dpi=150, bbox_inches='tight')
            return figure

        class _DashboardWindow(QWidget):
            def __init__(self, visualizer, selectable_players):
                super().__init__()
                self.visualizer = visualizer
                self.selectable_players = selectable_players

                self.setWindowTitle('Game Data Visualizer')
                self.resize(1400, 960)

                root_layout = QGridLayout()
                root_layout.setHorizontalSpacing(14)
                root_layout.setVerticalSpacing(14)

                self.game_type_panel, self.game_type_combo, self.game_type_figure, self.game_type_canvas = self._create_chart_panel(
                    'Game Type Distribution',
                    selectable_players,
                    self._on_game_type_player_changed
                )
                self.win_loss_panel, self.win_loss_combo, self.win_loss_figure, self.win_loss_canvas = self._create_chart_panel(
                    'Wins vs Losses',
                    selectable_players,
                    self._on_win_loss_player_changed
                )
                self.losses_panel, self.losses_combo, self.losses_figure, self.losses_canvas = self._create_chart_panel(
                    'Losses by Bot',
                    selectable_players,
                    self._on_losses_player_changed
                )

                summary_panel = QGroupBox('Player Summary (Static)')
                summary_layout = QVBoxLayout()
                summary_layout.addWidget(self.visualizer._build_summary_table_widget(game_type_filter=game_type_filter))
                summary_panel.setLayout(summary_layout)

                root_layout.addWidget(self.game_type_panel, 0, 0)
                root_layout.addWidget(self.win_loss_panel, 0, 1)
                root_layout.addWidget(self.losses_panel, 1, 0)
                root_layout.addWidget(summary_panel, 1, 1)
                self.setLayout(root_layout)

                # Initial rendering for each independent chart/player selector.
                self._on_game_type_player_changed(self.game_type_combo.currentText())
                self._on_win_loss_player_changed(self.win_loss_combo.currentText())
                self._on_losses_player_changed(self.losses_combo.currentText())

            def _create_chart_panel(self, title, players_list, on_change):
                panel = QGroupBox(title)
                panel_layout = QVBoxLayout()

                controls = QHBoxLayout()
                controls.addWidget(QLabel('Player:'))
                combo = QComboBox()
                combo.addItems(players_list)
                combo.currentTextChanged.connect(on_change)
                controls.addWidget(combo)
                controls.addStretch(1)

                figure = Figure(figsize=(5.8, 4.3))
                canvas = FigureCanvas(figure)
                canvas.setMinimumHeight(320)

                panel_layout.addLayout(controls)
                panel_layout.addWidget(canvas)
                panel.setLayout(panel_layout)
                return panel, combo, figure, canvas

            def _on_game_type_player_changed(self, player_name):
                if not player_name:
                    return
                self.visualizer._draw_game_type_distribution(
                    self.game_type_figure,
                    player_name,
                    game_type_filter=game_type_filter,
                )
                self.game_type_canvas.draw_idle()

            def _on_win_loss_player_changed(self, player_name):
                if not player_name:
                    return
                self.visualizer._draw_wins_losses(
                    self.win_loss_figure,
                    player_name,
                    game_type_filter=game_type_filter,
                )
                self.win_loss_canvas.draw_idle()

            def _on_losses_player_changed(self, player_name):
                if not player_name:
                    return
                self.visualizer._draw_losses_by_bot(
                    self.losses_figure,
                    player_name,
                    game_type_filter=game_type_filter,
                )
                self.losses_canvas.draw_idle()

        app = QApplication.instance()
        created_app = False
        if app is None:
            app = QApplication(sys.argv)
            created_app = True

        window = _DashboardWindow(self, selectable_players)
        window.show()

        if created_app:
            app.exec_()

        return window
    
def __main__():
    db=gameDatabase()
    # db.initialize_database()
    # db.migrate_player_table()
    # db.debug_show_tables_and_columns()
    # playerList=db.get_players()
    # print(playerList)
    # leaderboard=db.get_leaderboard()
    # print("\nLeaderboard:")
    # for rank, (username, winnings) in enumerate(leaderboard, start=1):
    #     print(f"{rank}. {username} - Total Winnings: {winnings}")
    visualizer = DatabaseVisualizer(db)
    visualizer.show_data_visualizer()
    #db.debug_get_dev_info()
    #db.debug_get_table_data()
if __name__ == "__main__":
    __main__()
    pass
