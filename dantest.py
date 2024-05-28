import pandas as pd
import random
import os
from typing import List, Tuple
import uuid

from catanatron_core.catanatron.models.enums import ActionType
from catanatron_core.catanatron import Player, Color, GameAccumulator
from catanatron_core.catanatron.game import Game
from catanatron_core.catanatron.state_functions import player_key, get_actual_victory_points



class RandomPlayer(Player):
    def decide(self, game, playable_actions):
        # This bot just picks a random action
        return random.choice(playable_actions)

class ResourceHoarderPlayer(Player):
    def decide(self, game, playable_actions):
        # This bot always tries to build a settlement if it can
        for action in playable_actions:
            if action[0] == ActionType.BUILD_SETTLEMENT:
                return action

        # If it can't build a settlement, it tries to build a road
        for action in playable_actions:
            if action[0] == ActionType.BUILD_ROAD:
                return action

        # If it can't build a settlement or a road, it picks a random action
        return random.choice(playable_actions)

class DataAccumulator(GameAccumulator):
    def __init__(self):
        self.data = []
        self.player_classes = {}
        
    def before(self, game: Game):
        self.turn = 0
        self.colors = game.state.colors
        self.player_classes = {color: player.__class__.__name__ for player, color in zip(game.state.players, game.state.colors)}
        
    def step(self, game_before_action, action):
        turn_info = [self.turn]
        for color in self.colors:
            vp = get_actual_victory_points(game_before_action.state, color)
            turn_info.append(vp)
        self.data.append(turn_info)
        self.turn += 1

    def after(self, game: Game):
        # This method can be used to finalize any data collection if needed
        pass

def run_game(players: List[Player]) -> pd.DataFrame:
    accumulator = DataAccumulator()
    game = Game(players)
    game.play(accumulators=[accumulator])

    # Create a DataFrame to store turn-by-turn information
    columns = ['Turn'] + [f'{color}_VP' for color in accumulator.colors]
    victory_points_df = pd.DataFrame(accumulator.data, columns=columns)
    
    # Add player class names as metadata columns
    for color, class_name in accumulator.player_classes.items():
        victory_points_df[f'{color}_Class'] = class_name
    
    # Add game-level metadata
    victory_points_df['Num_Players'] = len(players)
    victory_points_df['Num_Turns'] = accumulator.turn
    victory_points_df['Winner'] = game.winning_color()
    
    return victory_points_df

def save_game_results(df: pd.DataFrame, game_id: int, directory: str = "game_results"):
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, f"game_{game_id}.csv")
    df.to_csv(file_path, index=False)

def collect_multiple_games(games_config) -> pd.DataFrame:
    all_games_data = []
    for config in games_config:
        players = config['players']
        game_id = config.get('game_id', len(all_games_data) + 1)
        df = run_game(players)
        df['Game_ID'] = game_id
        save_game_results(df, game_id)
        all_games_data.append(df)
    
    # Concatenate all game results into a single DataFrame
    all_games_df = pd.concat(all_games_data, ignore_index=True)
    return all_games_df

# Example of running multiple games with different configurations
games_config = [
    {'players': [RandomPlayer(Color.RED), ResourceHoarderPlayer(Color.BLUE)], 'game_id': str(uuid.uuid4())},
    {'players': [ResourceHoarderPlayer(Color.RED), RandomPlayer(Color.BLUE)], 'game_id': str(uuid.uuid4())},
    # Add more game configurations as needed
]

# Collect and print results from multiple games
all_games_results = collect_multiple_games(games_config)
print(all_games_results)