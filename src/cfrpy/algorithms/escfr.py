from typing import cast, Generic
from typing import Dict, Callable
from dataclasses import dataclass, field
import random

from ..game import Game, Player, I, A_inv
from .cfr import matching


# Externally Sampled CFR: a version of Monte Carlo CFR
# the idea is to sample chance's and the opponent's actions, but follow all
# of the player's actions. this is also simpler than CFR.
# http://mlanctot.info/files/papers/nips09mccfr.pdf
# http://mlanctot.info/files/papers/PhD_Thesis_MarcLanctot.pdf
@dataclass
class ESCFR(Generic[A_inv, I]):
    regrets: Dict[I, Dict[A_inv, float]] = field(default_factory=dict)
    strategies: Dict[I, Dict[A_inv, float]] = field(default_factory=dict)
    touched: int = 0

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), cast(Player, p), self.regrets, self.strategies)

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        regrets: Dict[I, Dict[A_inv, float]],
        strategies: Dict[I, Dict[A_inv, float]],
    ):
        self.touched += 1

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            action = game.sample()
            return self.walk(game.apply(action), player, regrets, strategies)

        infoset = game.infoset(game.active)
        actions = infoset.actions()

        if infoset not in regrets:
            regrets[infoset] = {action: 0 for action in actions}
        if infoset not in strategies:
            strategies[infoset] = {action: 0 for action in actions}

        R = regrets[infoset]
        S = strategies[infoset]

        strategy = matching(list(R.values()))

        if game.active != player:
            (action,) = random.choices(actions, weights=strategy)
            value = self.walk(game.apply(action), player, regrets, strategies)

            for action, p in zip(actions, strategy):
                S[action] += p

            return value

        cfs = {action: 0 for action in actions}
        value = 0

        for action, p in zip(actions, strategy):
            cf = self.walk(game.apply(action), player, regrets, strategies)
            cfs[action] = cf
            value += p * cf

        for action in actions:
            R[action] += cfs[action] - value

        return value
