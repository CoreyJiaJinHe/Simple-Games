# Simple Games

This project is a personal practice space where I recreate classic games to improve my coding skills.

## Current Status

### GUI games implemented
- Texas Hold Em Poker
- Five Card Poker
- Blackjack
- Minesweeper

### In progress
- Thirteen Card Poker

## Planned Games

- [x] Five Card Poker
- [x] Blackjack
- [x] Minesweeper
- [ ] Thirteen Card Poker
- [ ] Tic-Tac-Toe
- [ ] Snake
- [ ] Connect Four
- [ ] Sudoku

## Tech Stack
- Python
- PyQt5 (for GUI)

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the main game launcher:
   ```bash
   python main_window.py
   ```

## Notes
- Individual game modules are split across separate Python files.
- This repository is intended for learning and experimentation.

## Ideas for Future Games

### Beginner-friendly
- Tic-Tac-Toe (great for minimax AI)
- Hangman
- Rock Paper Scissors (best-of-N and stats)
- Memory Match / Concentration

### Intermediate
- Snake
- Connect Four
- 2048
- Tetris (rotation and collision practice)

### Advanced
- Checkers with forced captures
- Monopoly-lite board game simulator
- Tower Defense (pathfinding + wave logic)

## Recommended Next 10 (Ranked by Learning Value)

1. **Connect Four** — game state modeling + minimax/alpha-beta pruning.
2. **Snake** — real-time input, timers, collision detection, and game loop design.
3. **Tetris** — matrix/grid logic, rotation systems, and line-clearing rules.
4. **2048** — deterministic movement rules, merging mechanics, and board transforms.
5. **Sudoku** — puzzle generation/validation and backtracking solver fundamentals.
6. **Checkers** — turn-based rules engine, mandatory captures, multi-jump logic.
7. **Battleship** — hidden state, coordinate systems, and bot strategy layers.
8. **Othello (Reversi)** — directional scanning and strong AI practice.
9. **Chess (basic)** — piece move validation, check/checkmate detection, state complexity.
10. **Tower Defense** — pathfinding, wave scheduling, balancing, and entity systems.

## Other Tech Stacks to Explore

### Stay in Python, expand modules
- **Pygame**: better control over a custom game loop, animation, and sprite systems.
- **Arcade**: modern 2D framework with simpler APIs for visuals and physics.
- **Tkinter**: lightweight GUI alternative to compare event-driven patterns.
- **FastAPI + WebSockets**: add online scoreboards, multiplayer lobbies, or remote turns.

### JavaScript / TypeScript
- **Phaser + TypeScript**: strong choice for browser-based 2D games.
- **React + Canvas (or PixiJS)**: UI-heavy game dashboards with custom rendering.
- **Node.js + Socket.IO**: real-time multiplayer backend for turn-based games.

### C# / .NET
- **Unity (C#)**: full game engine workflow, scenes, physics, and deployment.
- **MonoGame**: code-first game development similar to XNA style.
- **WPF / .NET MAUI**: desktop GUI game tooling and cross-platform app structure.

### C++
- **SFML**: good entry point for graphics/audio/input with low-level control.
- **SDL2**: foundational multimedia library for engine-style architecture.

### Rust
- **Bevy**: ECS-based architecture for modern game engine concepts.
- **Macroquad**: lightweight framework for quick 2D prototypes.

### Suggested progression path
1. Build 2–3 more games in current Python + PyQt5 setup.
2. Rebuild one game in **Pygame** (focus on real-time loop + rendering).
3. Rebuild the same game in **Phaser + TypeScript** (web deployment + TS types).
4. Try **Unity** or **Bevy** for ECS/engine architecture experience.
