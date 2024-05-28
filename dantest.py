from catanatron_core.catanatron import Player, Color, Action, ActionType
from catanatron_core.catanatron.game import Game
from catanatron_core.catanatron.models.actions import BuildSettlementAction, BuildRoadAction
from catanatron_core.catanatron.models.enums import Resource
import random

class RandomPlayer(Player):
    def decide(self, game: Game, actions: list[Action]) -> Action:
        # This bot just picks a random action
        return random.choice(actions)

class ResourceHoarderPlayer(Player):
    def decide(self, game: Game, actions: list[Action]) -> Action:
        # This bot always tries to build a settlement if it can
        for action in actions:
            if isinstance(action, BuildSettlementAction):
                return action

        # If it can't build a settlement, it tries to build a road
        for action in actions:
            if isinstance(action, BuildRoadAction):
                return action

        # If it can't build a settlement or a road, it picks a random action
        return random.choice(actions)