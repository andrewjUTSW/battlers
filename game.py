import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game import FightingGame

if __name__ == "__main__":
    game = FightingGame()
    game.run()