from dataclasses import dataclass
import importlib
import argparse
import pickle

from zerosum.strategy import Tournament, Leader
from zerosum.pkr.abstraction.abstractions import Translation
from zerosum.pkr.game import Check, Call, Action


@dataclass
class BloodStrategy(Leader):
    def default(self, game: Translation):
        actions = game.infoset(game.active).actions()
        if Check() in actions:
            return Check()
        return Call()

    def translate(self, game: Translation, action: Action):
        return game.apply(action).history[-1]


def main():
    parser = argparse.ArgumentParser("cfr")
    parser.add_argument(
        "-s",
        "--strategies",
        nargs="+",
        required=True,
    )
    parser.add_argument("-n", type=int, required=True)
    args = parser.parse_args()

    strategies = []
    for strat in args.strategies:
        module = importlib.import_module(f".{strat}", package="blood")
        game = module.Abstraction

        with open(f"bloods/{strat}.pkl", "rb") as f:
            s = pickle.load(f).strategies

        strategies.append(lambda: BloodStrategy(s, game))

    tourney = Tournament(Translation, tuple(strategies), 1000)

    for _ in range(args.n):
        tourney.turn()
        print(tourney.elos)
        print(tourney.wins)
