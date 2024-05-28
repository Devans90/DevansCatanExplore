import pandas as pd
import random
import os
from typing import List, Tuple
import uuid
from itertools import cycle

from catanatron_core.catanatron.models.enums import ActionType
from catanatron_core.catanatron import Player, Color, GameAccumulator
from catanatron_core.catanatron.game import Game
from catanatron_core.catanatron.state_functions import player_key, get_actual_victory_points
from tqdm import tqdm

# Import additional accumulators
from catanatron_experimental.cli.accumulators import (
    JsonDataAccumulator,
    CsvDataAccumulator,
    StatisticsAccumulator,
    VpDistributionAccumulator,
)

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
        turn_info = {
            'Turn': self.turn,
            'Current_Player': game_before_action.state.current_color().name,
            'Num_Turns': game_before_action.state.num_turns,
            'Resource_Bank': game_before_action.state.resource_freqdeck,
            'Dev_Card_Bank': len(game_before_action.state.development_listdeck),
            'Actions_Taken': len(game_before_action.state.actions)
        }
        
        for color in self.colors:
            key = player_key(game_before_action.state, color)
            turn_info[f'{color.name}_VP'] = game_before_action.state.player_state[f"{key}_ACTUAL_VICTORY_POINTS"]
            turn_info[f'{color.name}_Settlements'] = len(game_before_action.state.buildings_by_color[color].get('SETTLEMENT', []))
            turn_info[f'{color.name}_Cities'] = len(game_before_action.state.buildings_by_color[color].get('CITY', []))
            turn_info[f'{color.name}_Roads'] = len(game_before_action.state.buildings_by_color[color].get('ROAD', []))
            turn_info[f'{color.name}_Dev_Cards'] = game_before_action.state.player_state[f"{key}_VICTORY_POINT_IN_HAND"]
            turn_info[f'{color.name}_Class'] = self.player_classes[color]
            
        self.data.append(turn_info)
        self.turn += 1

    def after(self, game: Game):
        # This method can be used to finalize any data collection if needed
        pass

def run_game(players: List[Player], accumulators: List[GameAccumulator]) -> pd.DataFrame:
    accumulator = DataAccumulator()
    all_accumulators = accumulators + [accumulator]
    game = Game(players)
    game.play(accumulators=all_accumulators)

    # Create a DataFrame to store turn-by-turn information
    victory_points_df = pd.DataFrame(accumulator.data)
    
    # Add game-level metadata
    victory_points_df['Num_Players'] = len(players)
    victory_points_df['Winner'] = game.winning_color().name if game.winning_color() else None
    
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

        # Initialize additional accumulators
        statistics_accumulator = StatisticsAccumulator()
        vp_accumulator = VpDistributionAccumulator()
        accumulators = [statistics_accumulator, vp_accumulator]

        df = run_game(players, accumulators)
        df['Game_ID'] = game_id
        save_game_results(df, game_id)
        all_games_data.append(df)
    
    # Concatenate all game results into a single DataFrame
    all_games_df = pd.concat(all_games_data, ignore_index=True)
    return all_games_df

# # Example of running multiple games with different configurations
# games_config = [
#     {'players': [RandomPlayer(Color.RED), ResourceHoarderPlayer(Color.BLUE)], 'game_id': 1},
#     {'players': [ResourceHoarderPlayer(Color.RED), RandomPlayer(Color.BLUE)], 'game_id': 2},
#     # Add more game configurations as needed
# ]


colors = cycle([Color.RED, Color.BLUE, Color.BLUE, Color.WHITE])

games_config = []
for i in tqdm(range(100), desc="Running games"):
    num_players = random.randint(2, 4)
    players = [RandomPlayer(next(colors)) for _ in range(num_players)]
    games_config.append({'players': players, 'game_id': uuid.uuid4()})
    # Collect and print results from multiple games
    all_games_results = []
    for config in games_config:
        players = config['players']
        game_id = config.get('game_id', len(all_games_results) + 1)

        # Initialize additional accumulators
        statistics_accumulator = StatisticsAccumulator()
        vp_accumulator = VpDistributionAccumulator()
        accumulators = [statistics_accumulator, vp_accumulator]

        df = run_game(players, accumulators)
        df['Game_ID'] = game_id
        save_game_results(df, game_id)
        all_games_results.append(df)

    # Concatenate all game results into a single DataFrame
    all_games_df = pd.concat(all_games_results, ignore_index=True)

# Collect and print results from multiple games
all_games_results = collect_multiple_games(games_config)
print(all_games_results)
